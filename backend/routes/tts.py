import uuid
import threading
from pathlib import Path
from dataclasses import dataclass, field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from auth import get_current_user_id
from db.client import get_supabase
from config import settings
from security.rate_limiter import check_rate_limit, SYNTHESIS_RULE, RateLimitExceeded
from ml.voice_engine import synthesize

router = APIRouter(prefix="/profiles/{profile_id}/tts", tags=["tts"])


@dataclass
class SynthesisJob:
    status: str = "pending"
    output_path: Path | None = None
    error: str | None = None


_jobs: dict[str, SynthesisJob] = {}
_jobs_lock = threading.Lock()


class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en"


class SynthesizeJobResponse(BaseModel):
    job_id: str
    status: str


def _run_synthesis(job_id: str, voice_model_ref: str, text: str, language: str):
    output_path = settings.synthesis_tmp_dir / f"{job_id}.wav"
    result = synthesize(voice_model_ref, text, output_path, language)

    with _jobs_lock:
        if result.success:
            _jobs[job_id] = SynthesisJob(status="complete", output_path=result.output_path)
        else:
            _jobs[job_id] = SynthesisJob(status="failed", error=result.error)


@router.post("", response_model=SynthesizeJobResponse)
def request_synthesis(
    profile_id: str,
    body: SynthesizeRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
):
    try:
        check_rate_limit(user_id, SYNTHESIS_RULE)
    except RateLimitExceeded as error:
        raise HTTPException(status_code=429, detail=str(error))

    supabase = get_supabase()
    result = (
        supabase.table("voice_profiles")
        .select("id, status, voice_model_ref")
        .eq("id", profile_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    profile = result.data[0]
    if profile["status"] != "ready":
        raise HTTPException(status_code=422, detail=f"Voice profile is not ready (status: {profile['status']})")

    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = SynthesisJob(status="processing")

    background_tasks.add_task(_run_synthesis, job_id, profile["voice_model_ref"], body.text, body.language)

    return SynthesizeJobResponse(job_id=job_id, status="processing")


@router.get("/jobs/{job_id}")
def get_job_status(profile_id: str, job_id: str, user_id: str = Depends(get_current_user_id)):
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"job_id": job_id, "status": job.status, "error": job.error}


@router.get("/jobs/{job_id}/audio")
def get_job_audio(profile_id: str, job_id: str, user_id: str = Depends(get_current_user_id)):
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "complete":
        raise HTTPException(status_code=409, detail=f"Job is not complete (status: {job.status})")

    response = FileResponse(job.output_path, media_type="audio/wav")

    with _jobs_lock:
        del _jobs[job_id]
    job.output_path.unlink(missing_ok=True)

    return response