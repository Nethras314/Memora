from typing import Optional
import logging

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

supabase_client = None
supabase_admin_client = None


def _anon_key() -> Optional[str]:
    return settings.SUPABASE_ANON_KEY or settings.SUPABASE_KEY


try:
    if settings.SUPABASE_URL and _anon_key():
        from supabase import create_client

        supabase_client = create_client(
            settings.SUPABASE_URL,
            _anon_key(),
        )
        logger.info("Supabase anon client initialized.")
    else:
        logger.warning("SUPABASE_URL or anon key not set. Using local fallback store.")
except Exception as e:
    logger.error(f"Failed to init Supabase anon client: {e}. Fallback active.")
    supabase_client = None

try:
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        from supabase import create_client as _create_admin

        supabase_admin_client = _create_admin(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("Supabase service-role client initialized.")
except Exception as e:
    logger.error(f"Failed to init Supabase admin client: {e}.")
    supabase_admin_client = None


def get_supabase():
    """Backward-compatible accessor. Prefers admin, falls back to anon, else None."""
    return supabase_admin_client or supabase_client


def get_supabase_admin():
    return supabase_admin_client or supabase_client


def is_supabase_configured() -> bool:
    return bool(settings.SUPABASE_URL and _anon_key())
