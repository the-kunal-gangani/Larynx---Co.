import time
import sys
from pathlib import Path
from TTS.api import TTS

REFERENCE_SAMPLES_DIR = Path("reference_samples")
OUTPUT_DIR = Path("test_outputs")
TEST_TEXT = "This is a test of my own cloned voice speaking a new sentence it has never heard before."

def get_reference_files():
    files = sorted(REFERENCE_SAMPLES_DIR.glob("*.wav"))
    if not files:
        print(f"No .wav files found in {REFERENCE_SAMPLES_DIR}")
        sys.exit(1)
    return [str(f) for f in files]

def run_clone_test(sample_count, tts_model):
    reference_files = get_reference_files()[:sample_count]
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"clone_{sample_count}_samples.wav"

    start = time.time()
    tts_model.tts_to_file(
        text=TEST_TEXT,
        speaker_wav=reference_files,
        language="en",
        file_path=str(output_path)
    )
    elapsed = time.time() - start

    print(f"Samples used: {sample_count}")
    print(f"Inference time: {elapsed:.2f}s")
    print(f"Output saved to: {output_path}")
    print("---")

def main():
    device = "cuda" if is_cuda_available() else "cpu"
    print(f"Running on: {device}")

    tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    for sample_count in [3, 10, 25]:
        run_clone_test(sample_count, tts_model)

def is_cuda_available():
    import torch
    return torch.cuda.is_available()

if __name__ == "__main__":
    main()