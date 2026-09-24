import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from ml.preprocess import preprocess_recording

INPUT_DIR = Path("preprocess_test_input")
OUTPUT_DIR = Path("preprocess_test_output")

def main():
    input_files = sorted(INPUT_DIR.glob("*"))
    if not input_files:
        print(f"No files found in {INPUT_DIR}")
        sys.exit(1)

    for input_path in input_files:
        print(f"Processing: {input_path.name}")
        result = preprocess_recording(input_path, OUTPUT_DIR)

        print(f"  Noise floor: {result.noise_floor_db:.2f} dB")
        print(f"  Noise check passed: {result.noise_check_passed}")
        print(f"  Segments produced: {len(result.segments)}")
        for segment_path in result.segments:
            print(f"    {segment_path.name}")
        print("---")

if __name__ == "__main__":
    main()