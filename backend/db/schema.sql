CREATE TYPE voice_profile_status AS ENUM ('collecting', 'training', 'ready', 'failed');
CREATE TYPE consent_type AS ENUM ('account_level', 'profile_level', 're_consent');
CREATE TYPE audit_action AS ENUM ('profile_created', 'recording_added', 'profile_trained', 'synthesis_requested', 'profile_deleted', 'account_deleted');

CREATE TABLE voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status voice_profile_status NOT NULL DEFAULT 'collecting',
    voice_model_ref TEXT,
    allow_raw_retention BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    trained_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE phrase_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    voice_profile_id UUID NOT NULL REFERENCES voice_profiles(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    duration_seconds NUMERIC NOT NULL,
    is_ownership_check BOOLEAN NOT NULL DEFAULT FALSE,
    noise_check_passed BOOLEAN,
    raw_audio_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE generated_clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    voice_profile_id UUID NOT NULL REFERENCES voice_profiles(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    source_text TEXT NOT NULL,
    duration_seconds NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    voice_profile_id UUID REFERENCES voice_profiles(id) ON DELETE SET NULL,
    consent_type consent_type NOT NULL,
    terms_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    voice_profile_id UUID,
    action audit_action NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_voice_profiles_user_id ON voice_profiles(user_id);
CREATE INDEX idx_phrase_recordings_voice_profile_id ON phrase_recordings(voice_profile_id);
CREATE INDEX idx_generated_clips_voice_profile_id ON generated_clips(voice_profile_id);
CREATE INDEX idx_generated_clips_expires_at ON generated_clips(expires_at);
CREATE INDEX idx_consent_records_user_id ON consent_records(user_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);

ALTER TABLE voice_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE phrase_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY voice_profiles_owner_access ON voice_profiles
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY phrase_recordings_owner_access ON phrase_recordings
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY generated_clips_owner_access ON generated_clips
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY consent_records_owner_access ON consent_records
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY audit_log_owner_access ON audit_log
    FOR SELECT USING (auth.uid() = user_id);