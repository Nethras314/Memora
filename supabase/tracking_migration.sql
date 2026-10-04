-- =========================================================
-- MEMORA - Cognitive Tracking Migration
-- Mood logs (BPSD), clinical notes, doctor access grants,
-- and the cognitive_sessions.game_type CHECK fix.
-- Run AFTER supabase/schema.sql and supabase/auth_migration.sql.
-- Safe to re-run (IF NOT EXISTS / DO blocks / additive).
-- =========================================================

-- 0. Fix cognitive_sessions.game_type CHECK -------------------------------
-- The API's ALLOWED_GAMES writes 'photo_recognition', but the original
-- schema CHECK allowed 'task_sequencing'. Align the CHECK with the API.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'cognitive_sessions_game_type_check'
    ) THEN
        ALTER TABLE public.cognitive_sessions DROP CONSTRAINT cognitive_sessions_game_type_check;
    END IF;
END $$;

ALTER TABLE public.cognitive_sessions
    ADD CONSTRAINT cognitive_sessions_game_type_check
    CHECK (game_type IN ('sequence_memory', 'general_knowledge', 'odd_one_out', 'photo_recognition'));

-- 1. MOOD LOGS (caregiver BPSD quick-log) ----------------------------------
CREATE TABLE IF NOT EXISTS public.mood_logs (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    mood TEXT NOT NULL CHECK (mood IN ('Calm', 'Happy', 'Anxious', 'Agitated', 'Confused', 'Sad', 'Irritable')),
    behavior_flags TEXT[] DEFAULT '{}',
    note TEXT,
    recorded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mood_logs_patient_time ON public.mood_logs(patient_id, created_at DESC);

-- 2. CLINICAL NOTES (doctor notes / care plan) -----------------------------
CREATE TABLE IF NOT EXISTS public.clinical_notes (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    note_type TEXT NOT NULL DEFAULT 'general' CHECK (note_type IN ('assessment', 'plan', 'general')),
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient_time ON public.clinical_notes(patient_id, created_at DESC);

-- 3. ACCESS GRANTS (consent / doctor access) --------------------------------
CREATE TABLE IF NOT EXISTS public.access_grants (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_access_grants_patient ON public.access_grants(patient_id);
CREATE INDEX IF NOT EXISTS idx_access_grants_doctor ON public.access_grants(doctor_id);

-- Only one active grant per (patient, doctor) pair.
CREATE UNIQUE INDEX IF NOT EXISTS idx_access_grants_active_unique
    ON public.access_grants (patient_id, doctor_id)
    WHERE status = 'active';

-- 4. Restrict doctor access to granted patients ----------------------------
-- Replaces the unconditional `role = 'doctor'` branch in auth_migration.sql.
CREATE OR REPLACE FUNCTION public.can_access_patient(pid BIGINT)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
    SELECT COALESCE((
        SELECT TRUE FROM public.patients p
        WHERE p.id = pid
          AND (
            public.is_admin()
            OR p.caregiver_id = auth.uid()
            OR p.auth_user_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.profiles pr
                WHERE pr.id = auth.uid()
                  AND pr.role = 'doctor'
                  AND EXISTS (
                    SELECT 1 FROM public.access_grants g
                    WHERE g.patient_id = pid
                      AND g.doctor_id = auth.uid()
                      AND g.status = 'active'
                  )
            )
            OR EXISTS (
                SELECT 1 FROM public.profiles pr
                WHERE pr.id = auth.uid()
                  AND pr.role = 'patient'
                  AND pr.linked_patient_id = pid
            )
          )
        LIMIT 1
    ), FALSE)
$$;

-- 5. RLS policies for the new tables ----------------------------------------
ALTER TABLE public.mood_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinical_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.access_grants ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Role-scoped mood logs" ON public.mood_logs;
CREATE POLICY "Role-scoped mood logs" ON public.mood_logs
    FOR ALL USING (public.can_access_patient(patient_id))
    WITH CHECK (public.can_access_patient(patient_id));

DROP POLICY IF EXISTS "Role-scoped clinical notes" ON public.clinical_notes;
CREATE POLICY "Role-scoped clinical notes" ON public.clinical_notes
    FOR ALL USING (public.can_access_patient(patient_id))
    WITH CHECK (public.can_access_patient(patient_id));

DROP POLICY IF EXISTS "Grant read" ON public.access_grants;
CREATE POLICY "Grant read" ON public.access_grants
    FOR SELECT USING (
        public.is_admin()
        OR doctor_id = auth.uid()
        OR granted_by = auth.uid()
        OR public.can_access_patient(patient_id)
    );

DROP POLICY IF EXISTS "Grant write" ON public.access_grants;
CREATE POLICY "Grant write" ON public.access_grants
    FOR INSERT WITH CHECK (public.is_admin() OR granted_by = auth.uid());

DROP POLICY IF EXISTS "Grant update" ON public.access_grants;
CREATE POLICY "Grant update" ON public.access_grants
    FOR UPDATE USING (public.is_admin() OR granted_by = auth.uid())
    WITH CHECK (public.is_admin() OR granted_by = auth.uid());
