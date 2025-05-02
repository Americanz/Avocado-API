from supabase import create_client, Client
from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client() -> Client:
    """
    Returns a Supabase client instance
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)
