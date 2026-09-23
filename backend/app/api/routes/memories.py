import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from typing import List, Optional
from backend.app.models.schemas import MemoryResponse
from backend.app.core import database as db_module
from backend.app.core.access import can_write, ensure_patient_access
from backend.app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["Memory Bank"])

# In-memory fallback store for offline development / testing
MOCK_MEMORIES = [
    {
        "id": 1,
        "patient_id": 1,
        "category": "Person",
        "title": "Daughter",
        "details": "Anitha is my loving daughter who prepares herbal tea for me.",
        "relationship": "Daughter",
        "photo_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": 2,
        "patient_id": 1,
        "category": "Food",
        "title": "Favourite Food",
        "details": "Hot Idli with fresh coconut and coriander chutney.",
        "relationship": "Food",
        "photo_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": 3,
        "patient_id": 1,
        "category": "Place",
        "title": "Village Home",
        "details": "Our childhood home in Thanjavur with the courtyard and swing.",
        "relationship": "Home",
        "photo_url": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80"
    }
]

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
IMAGE_EXT_BY_TYPE = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024
ALLOWED_CATEGORIES = {"Person", "Place", "Food", "Activity", "Important Memory"}
PLACEHOLDER_PHOTO = "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80"


def _supabase():
    return db_module.get_supabase_admin() if db_module.is_supabase_configured() else None


def _photo_ext(photo: Optional[UploadFile]) -> str:
    content_type = ((photo.content_type if photo else None) or "").lower()
    if content_type in IMAGE_EXT_BY_TYPE:
        return IMAGE_EXT_BY_TYPE[content_type]
    raw = (photo.filename.rsplit(".", 1)[-1].lower() if photo and photo.filename and "." in photo.filename else "jpg")
    return raw if raw in ("jpg", "jpeg", "png", "webp") else "jpg"


async def _upload_photo(supabase, prefix: str, patient_id: int, user_id: str, photo: Optional[UploadFile]) -> Optional[str]:
    if photo is None or not photo.filename:
        return None
    content_type = (photo.content_type or "").lower()
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Photo must be JPEG, PNG or WebP.")
    try:
        file_bytes = await photo.read()
    except Exception as exc:
        logger.warning(f"Error reading uploaded photo file: {exc}")
        return None
    if not file_bytes:
        return None
    if len(file_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=400, detail="Photo must be under 5 MB.")
    if supabase is None:
        return None
    ext = _photo_ext(photo)
    safe_filename = f"{prefix}_{patient_id}_{(user_id or 'anon')[:8]}_{uuid.uuid4().hex[:10]}.{ext}"
    try:
        supabase.storage.from_("patient-memories").upload(
            safe_filename,
            file_bytes,
            {"content-type": content_type or f"image/{ext}"},
        )
        return supabase.storage.from_("patient-memories").get_public_url(safe_filename)
    except Exception as storage_err:
        logger.warning(f"Failed to upload photo to Supabase storage: {storage_err}")
        return None


@router.get("", response_model=List[MemoryResponse])
async def list_memories(patient_id: int = 1, user: dict = Depends(get_current_user)):
    """
    Returns personal memories specifically for the active patient from Supabase.
    """
    await ensure_patient_access(user, patient_id)
    supabase = _supabase()
    if supabase:
        try:
            res = supabase.table("memories").select("*").eq("patient_id", patient_id).order("id", desc=True).execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            logger.warning(f"Supabase memories fetch failed: {e}. Using fallback.")

    return [m for m in MOCK_MEMORIES if m["patient_id"] == patient_id]

@router.post("", response_model=MemoryResponse)
async def create_memory(
    patient_id: int = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    details: str = Form(...),
    relationship: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
):
    """
    Adds a new memory to the patient's personal memory bank and persists it to Supabase PostgreSQL.
    If a photo is uploaded, stores it in Supabase Storage bucket 'patient-memories'.
    """
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot add memories for this patient.")
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from {sorted(ALLOWED_CATEGORIES)}.")
    if len((title or "").strip()) < 2 or len((details or "").strip()) < 2:
        raise HTTPException(status_code=400, detail="Title and details are required.")

    supabase = _supabase()
    photo_url = await _upload_photo(supabase, "p", patient_id, user.get("id", ""), photo)

    # Fallback placeholder if no photo was uploaded or upload failed
    if not photo_url:
        photo_url = PLACEHOLDER_PHOTO

    record = {
        "patient_id": patient_id,
        "category": category,
        "title": title.strip(),
        "details": details.strip(),
        "relationship": relationship or category,
        "photo_url": photo_url
    }

    # 1. Insert into Supabase table
    if supabase:
        try:
            res = supabase.table("memories").insert(record).execute()
            if res.data and len(res.data) > 0:
                logger.info(f"Successfully persisted new memory ID {res.data[0]['id']} in Supabase")
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to insert memory row into Supabase: {e}. Storing in mock.")

    # 2. Fallback to mock store
    next_id = max([m["id"] for m in MOCK_MEMORIES], default=0) + 1
    new_memory = {
        "id": next_id,
        **record,
    }
    MOCK_MEMORIES.insert(0, new_memory)
    return new_memory

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    patient_id: int = 1,
    category: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    details: Optional[str] = Form(None),
    relationship: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
):
    """
    Updates an existing memory record in Supabase.
    """
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot edit memories for this patient.")
    if category is not None and category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from {sorted(ALLOWED_CATEGORIES)}.")

    supabase = _supabase()
    photo_url = await _upload_photo(supabase, "edit", memory_id, user.get("id", ""), photo)

    updates = {}
    if category is not None: updates["category"] = category
    if title is not None: updates["title"] = title.strip()
    if details is not None: updates["details"] = details.strip()
    if relationship is not None: updates["relationship"] = relationship
    if photo_url is not None: updates["photo_url"] = photo_url

    # 1. Update in Supabase
    if supabase and updates:
        try:
            res = supabase.table("memories").update(updates).eq("id", memory_id).eq("patient_id", patient_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to update memory in Supabase: {e}")

    # 2. Fallback update in mock store
    for m in MOCK_MEMORIES:
        if m["id"] == memory_id and m["patient_id"] == patient_id:
            for k, v in updates.items():
                m[k] = v
            return m

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")

@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, patient_id: int = 1, user: dict = Depends(get_current_user)):
    """
    Deletes a memory record by ID from Supabase.
    """
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot delete memories for this patient.")
    supabase = _supabase()
    if supabase:
        try:
            supabase.table("memories").delete().eq("id", memory_id).eq("patient_id", patient_id).execute()
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id} from Supabase: {e}")

    # Also remove from mock store
    global MOCK_MEMORIES
    MOCK_MEMORIES = [m for m in MOCK_MEMORIES if not (m["id"] == memory_id and m["patient_id"] == patient_id)]

    return {
        "success": True,
        "message": f"Memory {memory_id} deleted successfully."
    }
