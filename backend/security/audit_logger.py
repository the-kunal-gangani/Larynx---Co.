from db.client import get_supabase


def log_action(user_id: str, action: str, voice_profile_id: str | None = None, metadata: dict | None = None) -> None:
    supabase = get_supabase()
    supabase.table("audit_log").insert({
        "user_id": user_id,
        "voice_profile_id": voice_profile_id,
        "action": action,
        "metadata": metadata or {},
    }).execute()