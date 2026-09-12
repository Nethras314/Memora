from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from backend.app.models.schemas import MemoryResponse, MemoryCreate
from backend.app.core.database import get_supabase

router = APIRouter(prefix="/memories", tags=["Memory Bank"])

# Mock store for instant demo and tests
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
    Returns personal memories specifically for the active patient.
    """
    if supabase:
        try:
            res = supabase.table("memories").select("*").eq("patient_id", patient_id).order("id", desc=True).execute()
            if res.data:
                return res.data
        except Exception:
            pass
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
    Adds a new memory to the patient's personal memory bank.
    Integrates with Supabase Storage for photo CDN hosting.
    """
    photo_url = "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80"
    
    if photo and supabase:
        try:
            # Upload to Supabase Storage bucket 'patient-memories'
            file_bytes = await photo.read()
            filename = f"p_{patient_id}_{photo.filename}"
            supabase.storage.from_("patient-memories").upload(filename, file_bytes)
            photo_url = supabase.storage.from_("patient-memories").get_public_url(filename)
        except Exception:
            pass

    new_memory = {
        "id": len(MOCK_MEMORIES) + 1,
        "patient_id": patient_id,
        "category": category,
        "title": title,
        "details": details,
        "relationship": relationship or category,
        "photo_url": photo_url
    }
    MOCK_MEMORIES.insert(0, new_memory)
    return new_memory
