from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user_id
from db.client import get_supabase

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentRequest(BaseModel):
    terms_version: str


class ConsentResponse(BaseModel):
    id: str
    consent_type: str
    terms_version: str


@router.post("/account", response_model=ConsentResponse)
def record_account_consent(body: ConsentRequest, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase()
    result = (
        supabase.table("consent_records")
        .insert({
            "user_id": user_id,
            "voice_profile_id": None,
            "consent_type": "account_level",
            "terms_version": body.terms_version,
        })
        .execute()
    )

    record = result.data[0]
    return ConsentResponse(
        id=record["id"],
        consent_type=record["consent_type"],
        terms_version=record["terms_version"],
    )


@router.post("/profile/{profile_id}", response_model=ConsentResponse)
def record_profile_consent(profile_id: str, body: ConsentRequest, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase()
    result = (
        supabase.table("consent_records")
        .insert({
            "user_id": user_id,
            "voice_profile_id": profile_id,
            "consent_type": "profile_level",
            "terms_version": body.terms_version,
        })
        .execute()
    )

    record = result.data[0]
    return ConsentResponse(
        id=record["id"],
        consent_type=record["consent_type"],
        terms_version=record["terms_version"],
    )