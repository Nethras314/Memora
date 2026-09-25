-- =========================================================
-- MEMORA - Supabase Seed (self-healing, SQL Editor safe)
-- Smart India Hackathon 2026 - Problem Statement SIH26003
--
-- Run this in the Supabase Dashboard → SQL Editor → New query.
-- It does not require an Auth user. If a profile exists, patients
-- are linked to it; otherwise caregiver_id is NULL.
-- =========================================================

-- 1. Make caregiver_id nullable so demo patients can exist
--    before any auth.users / profiles row is created.
ALTER TABLE public.patients
    ALTER COLUMN caregiver_id DROP NOT NULL;

-- Clear the placeholder UUID that triggered:
--   patients_caregiver_id_fkey  Key (caregiver_id)=(00000000-...)
--   is not present in table "profiles"
UPDATE public.patients
SET caregiver_id = NULL
WHERE caregiver_id IS NOT NULL
  AND caregiver_id NOT IN (SELECT id FROM public.profiles);

-- 2. RLS: caregivers see their patients, plus unassigned demo rows
DROP POLICY IF EXISTS "Caregivers can view assigned patients" ON public.patients;
CREATE POLICY "Caregivers can view assigned patients" ON public.patients
    FOR SELECT USING (caregiver_id = auth.uid() OR caregiver_id IS NULL);

DROP POLICY IF EXISTS "Caregivers can insert assigned patients" ON public.patients;
CREATE POLICY "Caregivers can insert assigned patients" ON public.patients
    FOR INSERT WITH CHECK (caregiver_id = auth.uid() OR caregiver_id IS NULL);

DROP POLICY IF EXISTS "Caregivers can update assigned patients" ON public.patients;
CREATE POLICY "Caregivers can update assigned patients" ON public.patients
    FOR UPDATE USING (caregiver_id = auth.uid() OR caregiver_id IS NULL)
    WITH CHECK (caregiver_id = auth.uid() OR caregiver_id IS NULL);

DROP POLICY IF EXISTS "Caregiver manage patient memories" ON public.memories;
CREATE POLICY "Caregiver manage patient memories" ON public.memories
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients
            WHERE patients.id = memories.patient_id
              AND (patients.caregiver_id = auth.uid() OR patients.caregiver_id IS NULL)
        )
    );

DROP POLICY IF EXISTS "Caregiver manage patient tasks" ON public.tasks;
CREATE POLICY "Caregiver manage patient tasks" ON public.tasks
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients
            WHERE patients.id = tasks.patient_id
              AND (patients.caregiver_id = auth.uid() OR patients.caregiver_id IS NULL)
        )
    );

DROP POLICY IF EXISTS "Caregiver manage patient reminders" ON public.reminders;
CREATE POLICY "Caregiver manage patient reminders" ON public.reminders
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients
            WHERE patients.id = reminders.patient_id
              AND (patients.caregiver_id = auth.uid() OR patients.caregiver_id IS NULL)
        )
    );

DROP POLICY IF EXISTS "Caregiver view patient cognitive telemetry" ON public.cognitive_sessions;
CREATE POLICY "Caregiver view patient cognitive telemetry" ON public.cognitive_sessions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients
            WHERE patients.id = cognitive_sessions.patient_id
              AND (patients.caregiver_id = auth.uid() OR patients.caregiver_id IS NULL)
        )
    );

-- 3. Seed patients. Subquery is NULL when profiles is empty (no FK violation).
INSERT INTO public.patients (id, caregiver_id, name, age, gender, phone, primary_language, pin_hash)
VALUES
    (
        1,
        (SELECT id FROM public.profiles ORDER BY created_at ASC LIMIT 1),
        'Meenakshi',
        70,
        'Female',
        '8056962028',
        'ta-IN',
        '1234'
    ),
    (
        2,
        (SELECT id FROM public.profiles ORDER BY created_at ASC LIMIT 1),
        'Raman',
        75,
        'Male',
        '9000000000',
        'en-IN',
        '1234'
    ),
    (
        3,
        (SELECT id FROM public.profiles ORDER BY created_at ASC LIMIT 1),
        'Bornali',
        68,
        'Female',
        '9100000001',
        'as-IN',
        '1234'
    ),
    (
        4,
        (SELECT id FROM public.profiles ORDER BY created_at ASC LIMIT 1),
        'Arati',
        72,
        'Female',
        '9200000002',
        'bn-IN',
        '1234'
    )
ON CONFLICT (id) DO UPDATE SET
    caregiver_id = COALESCE(
        EXCLUDED.caregiver_id,
        public.patients.caregiver_id
    ),
    name = EXCLUDED.name,
    age = EXCLUDED.age,
    gender = EXCLUDED.gender,
    phone = EXCLUDED.phone,
    primary_language = EXCLUDED.primary_language,
    pin_hash = EXCLUDED.pin_hash;

SELECT setval(
    pg_get_serial_sequence('public.patients', 'id'),
    COALESCE((SELECT MAX(id) FROM public.patients), 1)
);

-- 4. Re-seed related demo rows without needing unique constraints
--    (ON CONFLICT DO NOTHING only works when a unique index exists).
DELETE FROM public.cognitive_sessions WHERE patient_id IN (1, 2, 3, 4);
DELETE FROM public.reminders WHERE patient_id IN (1, 2, 3, 4);
DELETE FROM public.tasks WHERE patient_id IN (1, 2, 3, 4);
DELETE FROM public.memories WHERE patient_id IN (1, 2, 3, 4);

INSERT INTO public.memories (patient_id, category, title, details, relationship, photo_url)
VALUES
    (1, 'Person', 'Daughter', 'Anitha is my eldest daughter who takes care of me.', 'Daughter', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80'),
    (1, 'Food', 'Favourite Food', 'Hot steaming Idli with coconut chutney.', 'Food Preference', 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80'),
    (1, 'Place', 'Village Home', 'Our ancestral courtyard home in Thanjavur with the mango tree.', 'Childhood Home', 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80'),
    (2, 'Person', 'Son', 'Kumar is my supportive son.', 'Son', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80'),
    (3, 'Person', 'Daughter', 'Bornali loves her daughter who visits from Nagaon on weekends.', 'Daughter', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80'),
    (3, 'Food', 'Favourite Food', 'Warm pitha and laru during Bihu.', 'Food Preference', 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80'),
    (4, 'Person', 'Son', 'Arati lives near the Hooghly with her son who tends her garden.', 'Son', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80'),
    (4, 'Food', 'Favourite Food', 'Fish curry and rice, her Sunday favourite.', 'Food Preference', 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80');

INSERT INTO public.tasks (patient_id, title, task_time, category, done)
VALUES
    (1, 'Morning Breakfast & Warm Milk', '09:00', 'Routine', true),
    (1, 'Memory Symbol Game', '10:30', 'Cognitive', false),
    (1, 'Balanced Lunch & Rest', '13:00', 'Routine', false),
    (1, 'Gentle Courtyard Walk', '17:00', 'Exercise', false),
    (2, 'Morning Yoga & Breathing', '08:30', 'Exercise', true),
    (2, 'Afternoon Medicine', '13:30', 'Routine', false),
    (3, 'Morning tea on the verandah', '08:00', 'Routine', true),
    (3, 'Bihu song listening time', '16:00', 'Cognitive', false),
    (4, 'Water the garden plants', '09:30', 'Exercise', true),
    (4, 'Afternoon rest', '14:00', 'Routine', false);

ALTER TABLE public.reminders ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'Custom';
ALTER TABLE public.reminders ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE public.reminders ALTER COLUMN enabled SET DEFAULT TRUE;

INSERT INTO public.reminders (patient_id, title, reminder_time, frequency, category, done, enabled)
VALUES
    (1, 'Drink a glass of water', '08:30', 'Daily', 'Water/Hydration', true, true),
    (1, 'Take afternoon heart medicine', '14:00', 'Daily', 'Medicine', false, true),
    (1, 'Evening calming devotional music', '17:30', 'Daily', 'Custom', false, true),
    (2, 'Drink warm water', '09:00', 'Daily', 'Water/Hydration', true, true),
    (3, 'Take morning blood pressure tablet', '08:30', 'Daily', 'Medicine', false, true),
    (3, 'Evening pitha and tea', '17:00', 'Daily', 'Food/Meal', false, true),
    (4, 'Morning fish medicine', '09:00', 'Daily', 'Medicine', true, true),
    (4, 'Afternoon rest and reading', '14:30', 'Daily', 'Custom', false, true);

INSERT INTO public.cognitive_sessions (patient_id, game_type, difficulty_level, score, accuracy, reaction_time_ms, mistake_count)
VALUES
    (1, 'sequence_memory', 1, 100, 1.00, 3200, 0),
    (1, 'sequence_memory', 2, 85, 0.85, 4100, 1),
    (1, 'odd_one_out', 1, 100, 1.00, 2900, 0),
    (1, 'general_knowledge', 1, 90, 0.90, 3500, 0),
    (2, 'sequence_memory', 1, 95, 0.95, 3000, 0),
    (3, 'sequence_memory', 1, 88, 0.88, 3600, 1),
    (4, 'odd_one_out', 1, 100, 1.00, 2800, 0);
