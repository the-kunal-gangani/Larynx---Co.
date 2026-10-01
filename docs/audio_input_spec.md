# Audio Input Spec

## Basis

These values come from actual Phase 0 testing against XTTS-v2 (not assumptions). Cloning quality was validated at 3, 10, and 25 reference samples — all three produced usable, clean output. Inference timing was also measured on real hardware (CPU).

## Sample Count

- **Hard minimum**: 3 samples (enforced in `clone.py` via `MIN_SAMPLES_REQUIRED`) — below this, cloning is rejected outright with `InsufficientSamplesError`.
- **Recommended guided list length**: 15-20 phrases.
- **Reasoning**: Phase 0 showed that even 3 samples clone well on a single, consistent recording session. A guided list longer than the bare minimum is still worth keeping — not because quality needs it, but because it gives the model exposure to more phonetic variety (different sounds, intonations, sentence lengths), which should make the resulting voice reference more robust across arbitrary text the user later types, rather than just the specific style of the test phrases. 15-20 strikes a balance: enough variety without making the recording step feel like a long chore for someone who may already find speaking effortful.
- **Hard cap**: 30 phrases. Beyond this, additional samples add diminishing value and only increase recording burden and processing/storage overhead during the (temporary) raw-recording window.

## Sample Duration

- **Per-phrase target**: 10-15 seconds.
- Shorter clips risk not capturing enough vocal variety per sample; much longer clips increase the chance of mid-recording pauses, which get split by the preprocessing pipeline anyway (see `preprocess.py`).

## Accepted Input Formats

Raw input is never assumed to be clean `.wav`. Accepted formats by platform:

| Platform | Typical raw format |
|---|---|
| Web (MediaRecorder API) | `.webm` (Opus) |
| Mobile (Flutter) | `.m4a` (AAC) or `.wav`, depending on recording plugin |

All formats are converted to mono `.wav` at **22,050 Hz** via `ffmpeg` as the first step of `preprocess.py`, before any further processing happens.

## Noise Handling

- Noise is assessed via the spectrogram-based noise floor check in `preprocess.py` (`measure_noise_floor_db`).
- Current threshold: recordings with a noise floor above **-40 dB** fail the check and the user is asked to re-record in a quieter space.
- **This threshold is a starting estimate, not yet validated against real noisy recordings.** It should be tuned once `test_preprocess.py` has been run against a deliberately noisy sample alongside a clean one.

## Silence Handling

- Silence gaps are used to split a single recording into multiple usable segments (`split_on_silence` in `preprocess.py`).
- Minimum segment duration: **3 seconds** — shorter fragments are discarded rather than kept, since they add little training value and risk being just breath sounds or false starts.

## Inference Timing (measured, Phase 0)

- **First run**: ~5 minutes — this is a one-time cost, almost entirely the XTTS-v2 model weight download (~1.87 GB) plus initial model load. Not representative of ongoing usage.
- **Subsequent generations**: 1-2 minutes per synthesis, on CPU, after the model is already loaded in memory.

### Design implication for Phase 4

1-2 minutes is too long for a synchronous HTTP request — both from a backend timeout perspective and from a UX perspective (a user shouldn't stare at a frozen "generating..." spinner for two minutes on every request). This confirms the backend needs **async job handling** for synthesis requests, as flagged as an open question back in Phase 0:

- A synthesis request should return immediately with a job reference, not block until audio is ready.
- The client polls (or receives a push/websocket update) for completion, then fetches/streams the result once ready.
- If GPU hosting is used in production instead of CPU, these numbers would drop significantly — but the async design should hold regardless, since it protects against variable/slow inference regardless of hardware.