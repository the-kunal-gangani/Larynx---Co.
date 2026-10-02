import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from auth import get_current_user_id
from db.client import get_supabase
from config import settings
from security.consent_verification import verify_profile_consent, ConsentMissingError
from security.signed_urls import generate_signed_url, RECORDINGS_BUCKET
from security.audit_logger import log_action
from ml.preprocess import preprocess_recording
from ml.voice_engine import clone

router = APIRouter(prefix="/profiles/{profile_id}/recordings", tags=["recordings"])


class RecordingResponse(BaseModel):
    id: str
    duration_seconds: float
    noise_check_passed: bool
    playback_url: str


def _get_profile(profile_id: str, user_id: str) -> dict:
    supabase = get_supabase()
    result = (
        supabase.table("voice_profiles")
        .select("id, status, allow_raw_retention")
        .eq("id", profile_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return result.data[0]


@router.post("", response_model=list[RecordingResponse])
def upload_recording(
    profile_id: str,
    is_ownership_check: bool = False,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    profile = _get_profile(profile_id, user_id)

    try:
        verify_profile_consent(user_id, profile_id)
    except ConsentMissingError:
        raise HTTPException(status_code=403, detail="Profile-level consent required before recording")

    supabase = get_supabase()

    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_path = Path(tmp_dir) / file.filename
        with open(raw_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = preprocess_recording(raw_path, Path(tmp_dir) / "segments")

        if not result.noise_check_passed:
            raise HTTPException(
                status_code=422,
                detail="Recording did not pass the audio quality check. Please re-record in a quieter space.",
            )

        expires_at = None
        if not profile["allow_raw_retention"]:
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=settings.raw_audio_retention_hours)).isoformat()

        responses = []
        for index, segment_path in enumerate(result.segments):
            storage_path = f"{user_id}/{profile_id}/{segment_path.name}"

            with open(segment_path, "rb") as f:
                supabase.storage.from_(RECORDINGS_BUCKET).upload(storage_path, f.read())

            import librosa
            duration = librosa.get_duration(path=str(segment_path))

            row = (
                supabase.table("phrase_recordings")
                .insert({
                    "voice_profile_id": profile_id,
                    "user_id": user_id,
                    "storage_path": storage_path,
                    "duration_seconds": duration,
                    "is_ownership_check": is_ownership_check and index == 0,
                    "noise_check_passed": result.noise_check_passed,
                    "raw_audio_expires_at": expires_at,
                })
                .execute()
            )

            record = row.data[0]
            responses.append(RecordingResponse(
                id=record["id"],
                duration_seconds=record["duration_seconds"],
                noise_check_passed=record["noise_check_passed"],
                playback_url=generate_signed_url(storage_path),
            ))

    log_action(user_id, "recording_added", voice_profile_id=profile_id, metadata={"segment_count": len(responses)})

    return responses


@router.get("", response_model=list[RecordingResponse])
def list_recordings(profile_id: str, user_id: str = Depends(get_current_user_id)):
    _get_profile(profile_id, user_id)
    supabase = get_supabase()

    result = (
        supabase.table("phrase_recordings")
        .select("id, storage_path, duration_seconds, noise_check_passed")
        .eq("voice_profile_id", profile_id)
        .execute()
    )

    return [
        RecordingResponse(
            id=row["id"],
            duration_seconds=row["duration_seconds"],
            noise_check_passed=row["noise_check_passed"],
            playback_url=generate_signed_url(row["storage_path"]),
        )
        for row in result.data
    ]


@router.post("/train")
def train_profile(profile_id: str, user_id: str = Depends(get_current_user_id)):
    profile = _get_profile(profile_id, user_id)
    supabase = get_supabase()

    result = (
        supabase.table("phrase_recordings")
        .select("id, storage_path")
        .eq("voice_profile_id", profile_id)
        .eq("noise_check_passed", True)
        .execute()
    )

    if len(result.data) < settings.min_samples_required:
        raise HTTPException(
            status_code=422,
            detail=f"Need at least {settings.min_samples_required} validated recordings, have {len(result.data)}",
        )

    supabase.table("voice_profiles").update({"status": "training"}).eq("id", profile_id).execute()

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_paths = []
        for row in result.data:
            local_path = Path(tmp_dir) / Path(row["storage_path"]).name
            audio_bytes = supabase.storage.from_(RECORDINGS_BUCKET).download(row["storage_path"])
            with open(local_path, "wb") as f:
                f.write(audio_bytes)
            local_paths.append(local_path)

        clone_result = clone(profile_id, local_paths)

    if not clone_result.success:
        supabase.table("voice_profiles").update({"status": "failed"}).eq("id", profile_id).execute()
        raise HTTPException(status_code=422, detail=clone_result.error)

    supabase.table("voice_profiles").update({
        "status": "ready",
        "voice_model_ref": clone_result.voice_model_ref,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", profile_id).execute()

    log_action(user_id, "profile_trained", voice_profile_id=profile_id)

    if not profile["allow_raw_retention"]:
        for row in result.data:
            supabase.storage.from_(RECORDINGS_BUCKET).remove([row["storage_path"]])
        supabase.table("phrase_recordings").delete().eq("voice_profile_id", profile_id).execute()

    return {"status": "ready"}