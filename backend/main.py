from fastapi import FastAPI

from config import settings
from routes import profiles, recordings, tts, consent

settings.raw_recordings_tmp_dir.mkdir(parents=True, exist_ok=True)
settings.voice_references_root.mkdir(parents=True, exist_ok=True)
settings.synthesis_tmp_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Larynx & Co. API")

app.include_router(profiles.router)
app.include_router(recordings.router)
app.include_router(tts.router)
app.include_router(consent.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}