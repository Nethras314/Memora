from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings

# Import API routes
from backend.app.api.routes import (
    auth,
    patients,
    memories,
    routines,
    cognitive,
    voice,
    caregiver
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## MEMORA - AI-Based Cognitive & Daily-Life Assistance Platform for Elderly Dementia Patients
    **Smart India Hackathon 2026 (Problem Statement ID: SIH26003)**
    
    Production-grade backend built with **FastAPI**, **Supabase** (PostgreSQL, Auth & Storage), 
    and **Sarvam AI** for Indian regional language voice STT/TTS (Tamil, Hindi, Kannada, Telugu, English).
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS origins: explicit env list, else sensible localhost dev defaults.
_env_origins = [o.strip() for o in (settings.CORS_ORIGINS or "").split(",") if o.strip()]
_cors_origins = _env_origins or [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# CORS Middleware for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Route Handlers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patients.router, prefix=settings.API_V1_STR)
app.include_router(memories.router, prefix=settings.API_V1_STR)
app.include_router(routines.router, prefix=settings.API_V1_STR)
app.include_router(cognitive.router, prefix=settings.API_V1_STR)
app.include_router(voice.router, prefix=settings.API_V1_STR)
app.include_router(caregiver.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    return {
        "status": "online",
        "platform": "MEMORA Production Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
