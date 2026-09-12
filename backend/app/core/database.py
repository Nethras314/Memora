from typing import Optional, Dict, Any, List
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

supabase_client = None

try:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        from supabase import create_client, Client
        supabase_client: Optional[Client] = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client successfully initialized.")
    else:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set. Using local in-memory fallback store.")
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {e}. Fallback active.")

def get_supabase():
    """
    Dependency to get the active Supabase client.
    Returns None if not configured.
    """
    return supabase_client
