import shutil
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user_id
from db.client import get_supabase
from config import settings
from security.consent_verification import verify_account_consent, ConsentMissingError
from security.rate_limiter import check_rate_limit, PROFILE_CREATION_RULE, RateLimitExceeded
from security.audit_logger import log_action

router = APIRouter(prefix="/profiles", tags=["profiles"])


class CreateProfileRequest(BaseModel):
    name: str


class ProfileResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str


@router.post("", response_model=ProfileResponse)
def create_profile(body: CreateProfileRequest, user_id: str = Depends(get_current_user_id)):
    try:
        verify_account_consent(user_id)
    except ConsentMissingError:
        raise HTTPException(status_code=403, detail="Account-level consent required before creating a profile")

    try:
        check_rate_limit(user_id, PROFILE_CREATION_RULE)
    except RateLimitExceeded as error:
        raise HTTPException(status_code=429, detail=str(error))

    supabase = get_supabase()
    result = (
        supabase.table("voice_profiles")
        .insert({"user_id": user_id, "name": body.name, "status": "collecting"})
        .execute()
    )

    profile = result.data[0]
    log_action(user_id, "profile_created", voice_profile_id=profile["id"])

    return ProfileResponse(
        id=profile["id"],
        name=profile["name"],
        status=profile["status"],
        created_at=profile["created_at"],
    )


@router.get("", response_model=list[ProfileResponse])
def list_profiles(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase()
    result = (
        supabase.table("voice_profiles")
        .select("id, name, status, created_at")
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .execute()
    )

    return [ProfileResponse(**row) for row in result.data]


@router.delete("/{profile_id}")
def delete_profile(profile_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase()
    result = (
        supabase.table("voice_profiles")
        .select("id")
        .eq("id", profile_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    reference_dir = settings.voice_references_root / profile_id
    if reference_dir.exists():
        shutil.rmtree(reference_dir)

    supabase.table("voice_profiles").delete().eq("id", profile_id).execute()

    log_action(user_id, "profile_deleted", voice_profile_id=profile_id)

    return {"deleted": True}