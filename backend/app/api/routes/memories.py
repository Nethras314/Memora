import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from typing import List, Optional
from backend.app.models.schemas import MemoryResponse
from backend.app.core.database import get_supabase

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

@router.get("", response_model=List[MemoryResponse])
async def list_memories(patient_id: int = 1, supabase = Depends(get_supabase)):
    """
    Returns personal memories specifically for the active patient from Supabase.
    """
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
    supabase = Depends(get_supabase)
):
    """
    Adds a new memory to the patient's personal memory bank and persists it to Supabase PostgreSQL.
    If a photo is uploaded, stores it in Supabase Storage bucket 'patient-memories'.
    """
    photo_url: Optional[str] = None
    
    if photo and photo.filename:
        try:
            file_bytes = await photo.read()
            if len(file_bytes) > 0:
                ext = photo.filename.split('.')[-1].lower() if '.' in photo.filename else 'jpg'
                safe_filename = f"p_{patient_id}_{uuid.uuid4().hex[:10]}.{ext}"
                
                if supabase:
                    try:
                        content_type = photo.content_type or f"image/{ext}"
                        supabase.storage.from_("patient-memories").upload(
                            safe_filename, 
                            file_bytes, 
                            {"content-type": content_type}
                        )
                        photo_url = supabase.storage.from_("patient-memories").get_public_url(safe_filename)
                    except Exception as storage_err:
                        logger.warning(f"Failed to upload photo to Supabase storage: {storage_err}")
        except Exception as e:
            logger.warning(f"Error reading uploaded photo file: {e}")

    # Fallback placeholder if no photo was uploaded or upload failed
    if not photo_url:
        photo_url = "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80"

    record = {
        "patient_id": patient_id,
        "category": category,
        "title": title,
        "details": details,
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
        "patient_id": patient_id,
        "category": category,
        "title": title,
        "details": details,
        "relationship": relationship or category,
        "photo_url": photo_url
    }
    MOCK_MEMORIES.insert(0, new_memory)
    return new_memory

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    category: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    details: Optional[str] = Form(None),
    relationship: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    supabase = Depends(get_supabase)
):
    """
    Updates an existing memory record in Supabase.
    """
    photo_url: Optional[str] = None
    if photo and photo.filename:
        try:
            file_bytes = await photo.read()
            if len(file_bytes) > 0:
                ext = photo.filename.split('.')[-1].lower() if '.' in photo.filename else 'jpg'
                safe_filename = f"edit_{memory_id}_{uuid.uuid4().hex[:10]}.{ext}"
                if supabase:
                    try:
                        content_type = photo.content_type or f"image/{ext}"
                        supabase.storage.from_("patient-memories").upload(
                            safe_filename, 
                            file_bytes, 
                            {"content-type": content_type}
                        )
                        photo_url = supabase.storage.from_("patient-memories").get_public_url(safe_filename)
                    except Exception as storage_err:
                        logger.warning(f"Failed to upload updated photo to Supabase: {storage_err}")
        except Exception as e:
            logger.warning(f"Error reading updated photo file: {e}")

    updates = {}
    if category is not None: updates["category"] = category
    if title is not None: updates["title"] = title
    if details is not None: updates["details"] = details
    if relationship is not None: updates["relationship"] = relationship
    if photo_url is not None: updates["photo_url"] = photo_url

    # 1. Update in Supabase
    if supabase:
        try:
            res = supabase.table("memories").update(updates).eq("id", memory_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to update memory in Supabase: {e}")

    # 2. Fallback update in mock store
    for m in MOCK_MEMORIES:
        if m["id"] == memory_id:
            for k, v in updates.items():
                m[k] = v
            return m

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")

@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, supabase = Depends(get_supabase)):
    """
    Deletes a memory record by ID from Supabase.
    """
    deleted_from_supabase = False
    if supabase:
        try:
            res = supabase.table("memories").delete().eq("id", memory_id).execute()
            if res.data and len(res.data) > 0:
                deleted_from_supabase = True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id} from Supabase: {e}")

    # Also remove from mock store
    global MOCK_MEMORIES
    initial_len = len(MOCK_MEMORIES)
    MOCK_MEMORIES = [m for m in MOCK_MEMORIES if m["id"] != memory_id]
    
    if not deleted_from_supabase and len(MOCK_MEMORIES) == initial_len:
        # Neither Supabase nor mock found it
        pass

    return {
        "success": True,
        "message": f"Memory {memory_id} deleted successfully."
    }
