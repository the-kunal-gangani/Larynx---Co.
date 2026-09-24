from pathlib import Path

_model = None


class SynthesisError(Exception):
    pass


def _get_model():
    global _model
    if _model is None:
        from TTS.api import TTS
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    return _model


def synthesize_speech(reference_dir: Path, text: str, language: str, output_path: Path) -> Path:
    reference_files = sorted(reference_dir.glob("*.wav"))
    if not reference_files:
        raise SynthesisError(f"No reference audio found in {reference_dir}")

    model = _get_model()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model.tts_to_file(
        text=text,
        speaker_wav=[str(f) for f in reference_files],
        language=language,
        file_path=str(output_path),
    )

    return output_path