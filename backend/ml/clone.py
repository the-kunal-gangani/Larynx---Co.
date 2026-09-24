import shutil
from pathlib import Path
from dataclasses import dataclass

MIN_SAMPLES_REQUIRED = 3


class InsufficientSamplesError(Exception):
    pass


@dataclass
class VoiceReference:
    profile_id: str
    reference_dir: Path
    sample_count: int


def build_voice_reference(profile_id: str, validated_audio_paths: list[Path], references_root: Path) -> VoiceReference:
    if len(validated_audio_paths) < MIN_SAMPLES_REQUIRED:
        raise InsufficientSamplesError(
            f"Need at least {MIN_SAMPLES_REQUIRED} validated samples, got {len(validated_audio_paths)}"
        )

    reference_dir = references_root / profile_id
    reference_dir.mkdir(parents=True, exist_ok=True)

    for index, audio_path in enumerate(validated_audio_paths):
        destination = reference_dir / f"sample_{index}.wav"
        shutil.copy(audio_path, destination)

    return VoiceReference(
        profile_id=profile_id,
        reference_dir=reference_dir,
        sample_count=len(validated_audio_paths),
    )