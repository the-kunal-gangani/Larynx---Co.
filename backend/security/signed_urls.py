from db.client import get_supabase

RECORDINGS_BUCKET = "phrase-recordings"
SIGNED_URL_EXPIRY_SECONDS = 300


def generate_signed_url(storage_path: str) -> str:
    supabase = get_supabase()
    result = supabase.storage.from_(RECORDINGS_BUCKET).create_signed_url(
        storage_path, SIGNED_URL_EXPIRY_SECONDS
    )
    return result["signedURL"]