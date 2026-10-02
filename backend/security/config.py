import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Settings:
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str
    raw_recordings_tmp_dir: Path
    voice_references_root: Path
    synthesis_tmp_dir: Path
    raw_audio_retention_hours: int
    min_samples_required: int
    tts_rate_limit_per_hour: int
    profile_creation_rate_limit_per_day: int


def load_settings() -> Settings:
    return Settings(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_key=os.environ["SUPABASE_SERVICE_KEY"],
        supabase_jwt_secret=os.environ["SUPABASE_JWT_SECRET"],
        raw_recordings_tmp_dir=Path(os.environ.get("RAW_RECORDINGS_TMP_DIR", "tmp/raw_recordings")),
        voice_references_root=Path(os.environ.get("VOICE_REFERENCES_ROOT", "voice_references")),
        synthesis_tmp_dir=Path(os.environ.get("SYNTHESIS_TMP_DIR", "tmp/synthesis")),
        raw_audio_retention_hours=int(os.environ.get("RAW_AUDIO_RETENTION_HOURS", "48")),
        min_samples_required=int(os.environ.get("MIN_SAMPLES_REQUIRED", "3")),
        tts_rate_limit_per_hour=int(os.environ.get("TTS_RATE_LIMIT_PER_HOUR", "30")),
        profile_creation_rate_limit_per_day=int(os.environ.get("PROFILE_CREATION_RATE_LIMIT_PER_DAY", "5")),
    )


settings = load_settings()