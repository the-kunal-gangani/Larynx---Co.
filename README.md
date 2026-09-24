# Larynx & Co. — Post-Illness Voice Banking

A voice-banking platform that lets patients facing voice loss (throat cancer, ALS, laryngectomy, and similar conditions) record their voice in advance, so future synthetic speech generated on their behalf still sounds like them — not a generic robotic text-to-speech voice.

Built as a self-hosted, privacy-first system. No third-party voice cloning APIs — cloning runs on an open-source model (XTTS-v2) under our own infrastructure, so voice data never leaves our system.

---

## Table of Contents

- [Problem](#problem)
- [Solution Overview](#solution-overview)
- [Core Principles](#core-principles)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Development Phases](#development-phases)
- [Security, Consent & Data Handling](#security-consent--data-handling)
- [Local Setup](#local-setup)
- [Status](#status)

---

## Problem

People who lose their voice due to illness or surgery currently rely on generic text-to-speech systems that sound nothing like them. This strips away a deeply personal part of their identity at an already difficult time. Voice cloning technology has matured enough to solve this — the gap is a properly engineered, consent-driven, privacy-respecting product that makes it accessible before treatment happens.

## Solution Overview

A patient records a set of guided phrases before undergoing treatment. Those recordings are used to train a personal voice model. Afterward, the patient (or a caregiver on their behalf) can type any text and generate speech in their own cloned voice — through a mobile app, a web app, or a quick-access phrase library for common needs.

## Core Principles

- **Self-hosted cloning** — no third-party API ever touches raw voice data
- **Consent-first** — no voice profile is created without explicit, verifiable consent
- **Privacy by design** — private storage, signed URLs, row-level access control, full deletion support
- **Explainable, not magical** — every stage of the pipeline (preprocessing, cloning, synthesis) is a testable, isolated module
- **Built in phases** — each layer is validated before the next one is built on top of it

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python) |
| Database & Auth | Supabase (Postgres + Row-Level Security) |
| Storage | Supabase Storage (private buckets, signed URLs) — training recordings only, never generated output |
| Voice Cloning | Coqui XTTS-v2 (self-hosted) |
| Audio Processing | librosa, soundfile |
| Mobile | Flutter |
| Web | Next.js |
| Mobile local history | App documents directory (audio files) + Hive/Isar/sqflite (metadata) |
| Web local history | IndexedDB (audio as Blob + metadata) |
| Background Jobs | FastAPI BackgroundTasks / job queue (TBD based on Phase 0 inference benchmarks) |

---

## Architecture

```
┌─────────────┐     ┌─────────────┐
│  Flutter App │     │  Next.js Web │
│  (local docs ││  (IndexedDB   │
│   + Hive)    ││   history)    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                  │
           ┌──────▼──────┐
           │   FastAPI    │
           │   Backend    │
           └──────┬──────┘
       ┌───────────┼───────────┐
       │           │           │
┌──────▼─────┐┌────▼─────┐┌────▼─────┐
│  Supabase  ││  Audio    ││  Voice    │
│  (Auth,DB, ││  Preproc  ││  Engine   │
│  Storage)  ││  Pipeline ││ (XTTS-v2) │
└────────────┘└──────────┘└───────────┘
```

The Voice Engine is wrapped behind a stable internal interface (`clone()`, `synthesize()`) so the underlying model can be swapped without touching anything above it.

Generated speech (TTS output) is streamed directly back to the client and never written to Supabase Storage or any backend table. If a user wants to keep a clip, it saves locally — to the app's documents directory on mobile, or to IndexedDB on web. Only training recordings (`phrase_recordings`) ever touch backend storage, and only until the voice profile finishes training.

---

## Project Structure

```
larynx-and-co/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── voice_profile.py
│   │   ├── recording.py
│   │   ├── consent_record.py
│   │   └── audit_log.py
│   │
│   ├── routes/
│   │   ├── profiles.py
│   │   ├── recordings.py
│   │   ├── tts.py
│   │   └── consent.py
│   │
│   ├── ml/
│   │   ├── voice_engine.py
│   │   ├── clone.py
│   │   ├── synthesize.py
│   │   └── preprocess.py
│   │
│   ├── security/
│   │   ├── rate_limiter.py
│   │   ├── audit_logger.py
│   │   ├── signed_urls.py
│   │   └── consent_verification.py
│   │
│   └── db/
│       ├── schema.sql
│       └── migrations/
│
├── mobile/
│   └── (Flutter project — local history via app documents dir + Hive/Isar/sqflite)
│
├── web/
│   └── (Next.js project — local history via IndexedDB)
│
├── research/
│   ├── test_clone.py
│   ├── reference_samples/
│   └── test_outputs/
│
├── docs/
│   ├── audio_input_spec.md
│   ├── consent_flow.md
│   ├── retention_policy.md
│   └── phase_notes/
│
├── requirements.txt
└── README.md
```

---

## Development Phases

### Phase 0 — Feasibility & Research
Validate XTTS-v2 cloning quality and inference speed on real hardware before building anything around it. Lock the audio input spec based on actual test results, not assumptions.

### Phase 0.5 — Security, Consent & Abuse Controls
Because this system handles voice identity data, security and consent are designed in before the data layer exists, not bolted on after:
- Explicit, recorded consent before any voice profile is created
- Liveness/ownership verification during recording (randomized phrases, not fixed scripts)
- Authentication and row-level authorization boundaries per user
- Private storage buckets, signed and time-limited audio URLs
- Full voice-profile deletion (raw recordings and trained reference — generated output was never stored server-side to begin with)
- Defined raw-recording retention policy
- Rate limits on both synthesis requests and profile-creation attempts
- Audit logging for profile creation, synthesis, and deletion events
- Safeguards against arbitrary/unauthorized cloning requests

### Phase 1 — Data Layer & Schema Design
Design the full schema — including consent and audit tables from Phase 0.5 — as versioned migrations, not ad-hoc table creation. Define storage folder conventions per user/profile before any upload code exists.

### Phase 2 — Audio Preprocessing Pipeline
A standalone, dependency-free module: raw audio in, cleaned audio out (silence trimmed, normalized, resampled). Tested against real recordings from varied environments before touching the rest of the app.

### Phase 3 — Voice Engine Wrapper
A stable abstraction (`clone()`, `synthesize()`) around XTTS-v2, with explicit handling for failure states (poor audio quality, insufficient samples) rather than silent garbage output.

### Phase 4 — Backend API
FastAPI routes built on top of the now-validated preprocessing and voice engine modules. Auth and authorization enforced from the first route written. Async job handling for cloning/synthesis if inference is slow.

### Phase 5 — Frontend (Flutter + Web)
Guided recording flow first — the highest-friction, most emotionally sensitive part of the product. Then TTS generation and playback. Then the quick-access phrase library for real-world use by patients with limited typing ability.

### Phase 6 — Polish & Deployment
Multiple voice profiles per account, client-side generation history (local documents dir + Hive/Isar/sqflite on mobile, IndexedDB on web), export, and production deployment — including a decision on GPU hosting based on real inference-cost numbers from Phase 0.

---

## Security, Consent & Data Handling

This system treats voice recordings as sensitive biometric identity data, not ordinary media files.

- **Consent is a first-class object**, not a checkbox afterthought — every voice profile links to a `consent_records` entry with a timestamp and the specific terms agreed to.
- **Ownership verification** happens at recording time via randomized phrase prompts, making it harder for someone to clone a voice from audio they don't have the right to use.
- **Access control** is enforced at the database level via row-level security, not just in application code — a backend bug should not be able to leak another user's voice data.
- **Storage** is private by default; audio is only ever accessed through short-lived signed URLs.
- **Deletion is real deletion** — removing a voice profile removes the raw recordings and the trained voice reference. Generated output audio is never stored server-side, so there's nothing to delete there — clearing it is a purely local/client-side action.
- **Every sensitive action is audited** — profile creation, synthesis requests, and deletions are logged with user, timestamp, and action for traceability.

Full detail lives in `docs/consent_flow.md` and `docs/retention_policy.md` as those are written out.

---

## Local Setup

```bash
git clone <repo-url>
cd larynx-and-co

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in Supabase project URL and keys

uvicorn backend.main:app --reload
```

Mobile and web setup instructions will be added once Phase 5 begins.

---

## Status

Currently in **Phase 0 — Feasibility & Research**. XTTS-v2 cloning quality and inference benchmarking in progress.