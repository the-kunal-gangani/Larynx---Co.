# Retention Policy

## Purpose

Defines how long each category of data is kept, and when/how it is deleted. Written to minimize the amount of sensitive voice data held at any given time, since retained raw audio is pure liability with no ongoing product value once a voice profile is successfully trained.

## Data Categories

### Raw Phrase Recordings
- **Retention**: discarded after the voice profile is successfully trained and validated, unless the user has opted in to allow retraining/improvement later
- **Rationale**: once XTTS-v2 has generated a voice reference from the samples, the raw audio itself has no further purpose in normal operation — keeping it only expands the amount of sensitive data at risk with no product benefit
- **Default**: raw recordings are deleted automatically within a short, defined window (e.g., 24-48 hours) after training completes successfully
- **Opt-in exception**: a user may choose to allow raw recordings to be retained specifically to support future re-training (e.g., if voice quality needs improvement later); this is off by default

### Trained Voice Reference (Voice Model)
- **Retention**: kept for as long as the voice profile is active
- **Deletion**: removed immediately and permanently when the user deletes the voice profile

### Generated Audio Clips (TTS Output)
- **Retention**: kept in the user's history up to a defined limit (count or time-based, e.g., last 90 days or last N clips), after which older clips auto-expire
- **Rationale**: generated clips are useful for the user's own reference/reuse but should not accumulate indefinitely, especially given free-tier storage constraints
- **User control**: users can manually delete any generated clip at any time, independent of the auto-expiry window

### Consent Records
- **Retention**: kept for the lifetime of the account, even after a voice profile is deleted
- **Rationale**: consent records are an audit trail, not user-facing content — they must persist independently of the data they authorized, so there is a record that consent was properly obtained even if the underlying voice data is later deleted

### Audit Logs
- **Retention**: kept for a defined period (e.g., 12 months) for traceability of profile creation, synthesis requests, and deletion events
- **Rationale**: supports abuse investigation and accountability without retaining the sensitive content itself (logs record that an action happened, not the audio content)

## Full Account/Profile Deletion

When a user deletes a voice profile:
1. Raw recordings (if any remain under the opt-in exception) are deleted
2. The trained voice reference is deleted
3. All generated audio clips tied to that profile are deleted
4. The `consent_records` entries for that profile are retained (per the Consent Records policy above) but marked as tied to a deleted profile
5. An audit log entry is created recording the deletion event itself

When a user deletes their entire account, the same cascade applies to every voice profile under that account.

## Storage Cost Consideration

Given free-tier storage constraints, retention windows also serve a practical cost-control purpose, not just a privacy one. Generated clips and any retained raw audio should be stored in compressed form (not uncompressed `.wav`) wherever the format isn't actively being processed by the voice engine.