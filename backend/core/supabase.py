from supabase import create_client, Client
from core.config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_supabase() -> Client:
    return get_supabase_client()
