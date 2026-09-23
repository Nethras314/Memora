from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.core import database as db_module
from backend.app.core.access import can_write, ensure_patient_access
from backend.app.core.security import get_current_user
from backend.app.models.schemas import MemoryResponse

router = APIRouter(prefix="/memories", tags=["Memory Bank"])

# Fallback store for local demo / tests (used only when Supabase is not configured)
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

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024
ALLOWED_CATEGORIES = {"Person", "Place", "Food", "Activity", "Important Memory"}


@router.get("", response_model=List[MemoryResponse])
async def list_memories(patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    if db_module.is_supabase_configured():
        admin = db_module.get_supabase_admin()
        try:
            res = admin.table("memories").select("*").eq("patient_id", patient_id).order("id", desc=True).execute()
            return res.data or []
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load memories: {exc}") from exc
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
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot add memories for this patient.")
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from {sorted(ALLOWED_CATEGORIES)}.")
    if len(title.strip()) < 2 or len(details.strip()) < 2:
        raise HTTPException(status_code=400, detail="Title and details are required.")

    photo_url = "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80"
    if photo is not None and photo.filename:
        if (photo.content_type or "") not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Photo must be JPEG, PNG or WebP.")
        file_bytes = await photo.read()
        if len(file_bytes) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=400, detail="Photo must be under 5 MB.")
        if db_module.is_supabase_configured():
            admin = db_module.get_supabase_admin()
            try:
                safe_name = "".join(c for c in photo.filename if c.isalnum() or c in (".", "-", "_"))[-60:]
                filename = f"p_{patient_id}_{user['id'][:8]}_{safe_name}"
                admin.storage.from_("patient-memories").upload(
                    filename, file_bytes, {"content-type": photo.content_type}
                )
                photo_url = admin.storage.from_("patient-memories").get_public_url(filename)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Photo upload failed: {exc}") from exc

    if db_module.is_supabase_configured():
        admin = db_module.get_supabase_admin()
        try:
            res = admin.table("memories").insert(
                {
                    "patient_id": patient_id,
                    "category": category,
                    "title": title.strip(),
                    "details": details.strip(),
                    "relationship": relationship or category,
                    "photo_url": photo_url,
                }
            ).execute()
            return (res.data or [{}])[0]
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to save memory: {exc}") from exc

    new_memory = {
        "id": max([m["id"] for m in MOCK_MEMORIES], default=0) + 1,
        "patient_id": patient_id,
        "category": category,
        "title": title.strip(),
        "details": details.strip(),
        "relationship": relationship or category,
        "photo_url": photo_url,
    }
    MOCK_MEMORIES.insert(0, new_memory)
    return new_memory


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, patient_id: int = 1, user: dict = Depends(get_current_user)):
    await ensure_patient_access(user, patient_id)
    if not can_write(user):
        raise HTTPException(status_code=403, detail="You cannot delete memories for this patient.")
    if db_module.is_supabase_configured():
        admin = db_module.get_supabase_admin()
        try:
            admin.table("memories").delete().eq("id", memory_id).eq("patient_id", patient_id).execute()
            return {"success": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Delete failed: {exc}") from exc
    global MOCK_MEMORIES
    MOCK_MEMORIES = [m for m in MOCK_MEMORIES if not (m["id"] == memory_id and m["patient_id"] == patient_id)]
    return {"success": True}
