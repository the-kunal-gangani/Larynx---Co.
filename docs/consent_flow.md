# Consent Flow

## Purpose

Voice recordings are biometric identity data. No voice profile may be created, and no recording may be used for cloning, without explicit, verifiable, recorded consent from the account holder.

## Consent Capture — When It Happens

1. **Account-level consent** — captured once, at account creation, before any recording flow is accessible. Covers acceptance of terms around how voice data is used, stored, and retained.
2. **Profile-level consent** — captured again immediately before the first recording of each new voice profile begins. This is separate from account-level consent because a single account may eventually manage multiple voice profiles (e.g., a caregiver managing a profile on behalf of a patient), and each profile's voice data needs its own explicit authorization.

## What Consent Confirms

The user explicitly confirms, in plain language, before recording begins:
- This is their own voice, or they have the legal right/permission to create a voice profile from this speaker's voice
- They understand the recordings will be used to train a personal voice model
- They understand how long raw recordings are retained (see `retention_policy.md`)
- They understand they can delete their voice profile and associated data at any time

## Ownership Verification

Consent alone does not verify that the speaker is who they claim to be. To reduce the risk of someone cloning a voice from audio they don't have rights to:

- During initial recording, the user is prompted to read back a **randomly generated phrase** (not a fixed, guessable script) as part of at least one sample
- This proves the recording is a live, on-the-spot reading by the person setting up the profile, not a replay of pre-existing audio someone found elsewhere

## Re-Consent Triggers

Consent is not a one-time checkbox that lasts forever. Re-confirmation is required when:
- A voice profile has been inactive (no new recordings, no generations) beyond a defined inactivity window
- The terms governing data use or retention change
- A new session attempts to add recordings to an existing profile after a significant gap

## Recording the Consent Event

Every consent action is stored as a `consent_records` entry, including:
- `user_id`
- `voice_profile_id` (null for account-level consent)
- `consent_type` (account-level / profile-level / re-consent)
- `timestamp`
- `terms_version` (which version of the terms text was shown)

This record exists so consent is auditable — not just claimed, but demonstrably given at a specific point in time against specific terms.

## What Is Not Covered Here

This document covers *consent to create and use a voice profile*. It does not cover payment terms, general account terms of service, or clinical/medical claims — those are handled separately if the product ever moves beyond a portfolio/demo stage.