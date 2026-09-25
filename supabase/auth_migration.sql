-- =========================================================
-- MEMORA - Multi-user Auth Migration (patient / caregiver / doctor / admin)
-- Run AFTER supabase/schema.sql in the Supabase SQL editor.
-- Safe to re-run (IF NOT EXISTS / additive changes only).
-- =========================================================

-- 1. Extend profile roles + patient linkage -------------------------------
ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS linked_patient_id BIGINT REFERENCES public.patients(id) ON DELETE SET NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'profiles_role_check'
    ) THEN
        ALTER TABLE public.profiles DROP CONSTRAINT profiles_role_check;
    END IF;
END $$;

ALTER TABLE public.profiles
    ADD CONSTRAINT profiles_role_check
    CHECK (role IN ('patient', 'caregiver', 'doctor', 'admin'));

-- 2. Patients: owner login + hashed PIN ------------------------------------
ALTER TABLE public.patients
    ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- 2b. Widen language support: add Assamese (as-IN) + Bengali (bn-IN) ----------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'patients_primary_language_check'
    ) THEN
        ALTER TABLE public.patients DROP CONSTRAINT patients_primary_language_check;
    END IF;
END $$;

ALTER TABLE public.patients
    ADD CONSTRAINT patients_primary_language_check
    CHECK (primary_language IN ('en-IN', 'ta-IN', 'hi-IN', 'kn-IN', 'te-IN', 'bn-IN', 'as-IN', 'mr-IN'));

-- caregiver_id stays nullable for demo rows; keep FK to profiles
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'patients_caregiver_fk'
    ) THEN
        ALTER TABLE public.patients
            ADD CONSTRAINT patients_caregiver_fk
            FOREIGN KEY (caregiver_id) REFERENCES public.profiles(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_patients_auth_user ON public.patients(auth_user_id);

-- 3. Auto-create profile row on signup --------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
    desired_role TEXT := COALESCE((NEW.raw_user_meta_data ->> 'role'), 'caregiver');
BEGIN
    IF desired_role = 'caretaker' THEN
        desired_role := 'caregiver';
    END IF;
    IF desired_role NOT IN ('patient', 'caregiver', 'doctor', 'admin') THEN
        desired_role := 'caregiver';
    END IF;

    INSERT INTO public.profiles (id, email, full_name, phone, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data ->> 'full_name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data ->> 'phone',
        desired_role
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name),
        role = EXCLUDED.role;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 4. Helper predicates -------------------------------------------------------
CREATE OR REPLACE FUNCTION public.current_role()
RETURNS TEXT
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid()
$$;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
    SELECT COALESCE((SELECT role = 'admin' FROM public.profiles WHERE id = auth.uid()), FALSE)
$$;

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

-- 5. RLS refresh --------------------------------------------------------------
-- profiles: self read/update; admins full read
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;

CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id OR public.is_admin());

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can manage profiles" ON public.profiles
    FOR ALL USING (public.is_admin()) WITH CHECK (public.is_admin());

-- patients
DROP POLICY IF EXISTS "Caregivers can view assigned patients" ON public.patients;
DROP POLICY IF EXISTS "Caregivers can insert assigned patients" ON public.patients;
DROP POLICY IF EXISTS "Caregivers can update assigned patients" ON public.patients;

CREATE POLICY "Multi-role patient read" ON public.patients
    FOR SELECT USING (public.can_access_patient(id));

CREATE POLICY "Caregiver patient insert" ON public.patients
    FOR INSERT WITH CHECK (
        public.is_admin()
        OR caregiver_id = auth.uid()
        OR (caregiver_id IS NULL AND public.current_role() IN ('caregiver', 'doctor'))
    );

CREATE POLICY "Caregiver patient update" ON public.patients
    FOR UPDATE USING (public.can_access_patient(id)) WITH CHECK (public.can_access_patient(id));

CREATE POLICY "Admin patient delete" ON public.patients
    FOR DELETE USING (public.is_admin());

-- memories / tasks / reminders / cognitive_sessions share one predicate
DROP POLICY IF EXISTS "Caregiver manage patient memories" ON public.memories;
DROP POLICY IF EXISTS "Caregiver manage patient tasks" ON public.tasks;
DROP POLICY IF EXISTS "Caregiver manage patient reminders" ON public.reminders;
DROP POLICY IF EXISTS "Caregiver view patient cognitive telemetry" ON public.cognitive_sessions;

CREATE POLICY "Role-scoped memories" ON public.memories
    FOR ALL USING (public.can_access_patient(patient_id))
    WITH CHECK (public.can_access_patient(patient_id));

CREATE POLICY "Role-scoped tasks" ON public.tasks
    FOR ALL USING (public.can_access_patient(patient_id))
    WITH CHECK (public.can_access_patient(patient_id));

CREATE POLICY "Role-scoped reminders" ON public.reminders
    FOR ALL USING (public.can_access_patient(patient_id))
    WITH CHECK (public.can_access_patient(patient_id));

CREATE POLICY "Role-scoped cognitive sessions" ON public.cognitive_sessions
    FOR ALL USING (public.can_access_patient(patient_id))
    WITH CHECK (public.can_access_patient(patient_id));

-- 6. Private storage bucket for memory photos ---------------------------------
INSERT INTO storage.buckets (id, name, public)
VALUES ('patient-memories', 'patient-memories', FALSE)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Role-scoped memory photo read" ON storage.objects;
DROP POLICY IF EXISTS "Role-scoped memory photo write" ON storage.objects;

CREATE POLICY "Role-scoped memory photo read" ON storage.objects
    FOR SELECT USING (bucket_id = 'patient-memories' AND auth.role() = 'authenticated');

CREATE POLICY "Role-scoped memory photo write" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'patient-memories' AND auth.role() = 'authenticated');
