from pathlib import Path
from dataclasses import dataclass

from ml.clone import build_voice_reference, InsufficientSamplesError
from ml.synthesize import synthesize_speech, SynthesisError
from config import settings


@dataclass
class CloneResult:
    success: bool
    voice_model_ref: str | None
    error: str | None


@dataclass
class SynthesisResult:
    success: bool
    output_path: Path | None
    error: str | None


def clone(profile_id: str, validated_audio_paths: list[Path]) -> CloneResult:
    try:
        reference = build_voice_reference(profile_id, validated_audio_paths, settings.voice_references_root)
        return CloneResult(success=True, voice_model_ref=str(reference.reference_dir), error=None)
    except InsufficientSamplesError as error:
        return CloneResult(success=False, voice_model_ref=None, error=str(error))


def synthesize(voice_model_ref: str, text: str, output_path: Path, language: str = "en") -> SynthesisResult:
    try:
        reference_dir = Path(voice_model_ref)
        result_path = synthesize_speech(reference_dir, text, language, output_path)
        return SynthesisResult(success=True, output_path=result_path, error=None)
    except SynthesisError as error:
        return SynthesisResult(success=False, output_path=None, error=str(error))