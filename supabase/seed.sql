-- =========================================================
-- MEMORA - Initial Seed Data for Supabase (Fixed & Self-Healing)
-- Smart India Hackathon 2026 - Problem Statement SIH26003
-- =========================================================

-- 1. Ensure caregiver_id is nullable for demo patients who do not have an auth account yet
ALTER TABLE public.patients ALTER COLUMN caregiver_id DROP NOT NULL;

-- 2. Update RLS policies to allow reading and managing demo patients (where caregiver_id IS NULL)
DROP POLICY IF EXISTS "Caregivers can view assigned patients" ON public.patients;
CREATE POLICY "Caregivers can view assigned patients" ON public.patients
    FOR SELECT USING (caregiver_id = auth.uid() OR caregiver_id IS NULL);

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

-- 3. Seed Patients (Meenakshi & Raman)
-- Uses existing profile ID if one exists, otherwise sets caregiver_id = NULL
INSERT INTO public.patients (id, caregiver_id, name, age, gender, phone, primary_language, pin_hash)
VALUES 
    (
        1,
        (SELECT id FROM public.profiles LIMIT 1),
        'Meenakshi',
        70,
        'Female',
        '8056962028',
        'ta-IN',
        '1234'
    ),
    (
        2,
        (SELECT id FROM public.profiles LIMIT 1),
        'Raman',
        75,
        'Male',
        '9000000000',
        'en-IN',
        '1234'
    )
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    age = EXCLUDED.age,
    gender = EXCLUDED.gender,
    primary_language = EXCLUDED.primary_language,
    pin_hash = EXCLUDED.pin_hash;

-- Reset patient ID auto-increment sequence
SELECT setval(pg_get_serial_sequence('public.patients', 'id'), COALESCE(MAX(id), 1)) FROM public.patients;

-- 4. Sample Memories for Meenakshi
INSERT INTO public.memories (patient_id, category, title, details, relationship, photo_url)
VALUES
    (1, 'Person', 'Daughter', 'Anitha is my eldest daughter who takes care of me.', 'Daughter', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80'),
    (1, 'Food', 'Favourite Food', 'Hot steaming Idli with coconut chutney.', 'Food Preference', 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80'),
    (1, 'Place', 'Village Home', 'Our ancestral courtyard home in Thanjavur with the mango tree.', 'Childhood Home', 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=400&q=80'),
    (2, 'Person', 'Son', 'Kumar is my supportive son.', 'Son', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80')
ON CONFLICT DO NOTHING;

-- 5. Sample Routine Tasks
INSERT INTO public.tasks (patient_id, title, task_time, category, done)
VALUES
    (1, 'Morning Breakfast & Warm Milk', '09:00', 'Routine', true),
    (1, 'Memory Symbol Game', '10:30', 'Cognitive', false),
    (1, 'Balanced Lunch & Rest', '13:00', 'Routine', false),
    (1, 'Gentle Courtyard Walk', '17:00', 'Exercise', false),
    (2, 'Morning Yoga & Breathing', '08:30', 'Exercise', true),
    (2, 'Afternoon Medicine', '13:30', 'Routine', false)
ON CONFLICT DO NOTHING;

-- 6. Sample Reminders
INSERT INTO public.reminders (patient_id, title, reminder_time, frequency, done)
VALUES
    (1, 'Drink a glass of water', '08:30', 'Daily', true),
    (1, 'Take afternoon heart medicine', '14:00', 'Daily', false),
    (1, 'Evening calming devotional music', '17:30', 'Daily', false),
    (2, 'Drink warm water', '09:00', 'Daily', true)
ON CONFLICT DO NOTHING;

-- 7. Sample Cognitive Baseline Telemetry (for DDA and Caregiver Trends)
INSERT INTO public.cognitive_sessions (patient_id, game_type, difficulty_level, score, accuracy, reaction_time_ms, mistake_count)
VALUES
    (1, 'sequence_memory', 1, 100, 1.00, 3200, 0),
    (1, 'sequence_memory', 2, 85, 0.85, 4100, 1),
    (1, 'odd_one_out', 1, 100, 1.00, 2900, 0),
    (1, 'general_knowledge', 1, 90, 0.90, 3500, 0),
    (2, 'sequence_memory', 1, 95, 0.95, 3000, 0)
ON CONFLICT DO NOTHING;
