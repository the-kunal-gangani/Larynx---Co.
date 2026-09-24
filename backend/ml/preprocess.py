import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import librosa
import soundfile as sf

TARGET_SAMPLE_RATE = 22050
MIN_SEGMENT_DURATION_SECONDS = 3.0
SILENCE_TOP_DB = 30
NOISE_FLOOR_THRESHOLD_DB = -40.0


@dataclass
class PreprocessResult:
    segments: list[Path]
    noise_check_passed: bool
    noise_floor_db: float


def convert_to_wav(input_path: Path, output_path: Path) -> Path:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-ac", "1",
            "-ar", str(TARGET_SAMPLE_RATE),
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    y, sr = librosa.load(str(path), sr=TARGET_SAMPLE_RATE, mono=True)
    return y, sr


def normalize_audio(y: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(y))
    if peak == 0:
        return y
    return y / peak * 0.95


def measure_noise_floor_db(y: np.ndarray, sr: int) -> float:
    intervals = librosa.effects.split(y, top_db=SILENCE_TOP_DB)
    silent_segments = []
    last_end = 0
    for start, end in intervals:
        if start > last_end:
            silent_segments.append(y[last_end:start])
        last_end = end
    if len(y) > last_end:
        silent_segments.append(y[last_end:])

    if not silent_segments:
        return -np.inf

    silence = np.concatenate(silent_segments)
    rms = np.sqrt(np.mean(silence ** 2)) if len(silence) > 0 else 0
    if rms == 0:
        return -np.inf
    return 20 * np.log10(rms)


def split_on_silence(y: np.ndarray, sr: int) -> list[np.ndarray]:
    intervals = librosa.effects.split(y, top_db=SILENCE_TOP_DB)
    min_samples = int(MIN_SEGMENT_DURATION_SECONDS * sr)

    segments = []
    for start, end in intervals:
        segment = y[start:end]
        if len(segment) >= min_samples:
            segments.append(segment)

    return segments if segments else [y]


def preprocess_recording(input_path: Path, output_dir: Path) -> PreprocessResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "converted.wav"
        convert_to_wav(input_path, wav_path)

        y, sr = load_audio(wav_path)
        noise_floor_db = measure_noise_floor_db(y, sr)
        noise_check_passed = noise_floor_db < NOISE_FLOOR_THRESHOLD_DB

        y = normalize_audio(y)
        segments = split_on_silence(y, sr)

        segment_paths = []
        for index, segment in enumerate(segments):
            segment_path = output_dir / f"{input_path.stem}_segment_{index}.wav"
            sf.write(str(segment_path), segment, sr)
            segment_paths.append(segment_path)

    return PreprocessResult(
        segments=segment_paths,
        noise_check_passed=noise_check_passed,
        noise_floor_db=noise_floor_db,
    )