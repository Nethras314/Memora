-- =========================================================
-- MEMORA - Supabase / PostgreSQL Production Schema
-- Smart India Hackathon 2026 - Problem Statement SIH26003
-- =========================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PROFILES (Caregivers / Clinicians / System Admins)
-- Linked to Supabase Auth (auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT DEFAULT 'caregiver' CHECK (role IN ('caregiver', 'doctor', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. PATIENTS
CREATE TABLE IF NOT EXISTS public.patients (
    id BIGSERIAL PRIMARY KEY,
    caregiver_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age INTEGER CHECK (age > 0 AND age < 130),
    gender TEXT CHECK (gender IN ('Male', 'Female', 'Other')),
    phone TEXT,
    primary_language TEXT DEFAULT 'en-IN' CHECK (primary_language IN ('en-IN', 'ta-IN', 'hi-IN', 'kn-IN', 'te-IN', 'bn-IN', 'mr-IN')),
    pin_hash TEXT NOT NULL, -- Hashed 4-digit PIN for private memory access
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. MEMORIES (Familiar people, places, foods, milestones)
CREATE TABLE IF NOT EXISTS public.memories (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('Person', 'Place', 'Food', 'Activity', 'Important Memory')),
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    relationship TEXT, -- Optional: 'Daughter', 'Son', 'Home', etc.
    photo_url TEXT,    -- Supabase Storage CDN URL (replaces bloated base64 blobs)
    audio_cue_url TEXT,-- Optional audio description
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. DAILY TASKS / ROUTINES
CREATE TABLE IF NOT EXISTS public.tasks (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    task_time TIME NOT NULL,
    category TEXT DEFAULT 'Daily' CHECK (category IN ('Daily', 'Routine', 'Exercise', 'Appointment', 'Cognitive')),
    done BOOLEAN DEFAULT FALSE,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. REMINDERS & NOTIFICATIONS
CREATE TABLE IF NOT EXISTS public.reminders (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    reminder_time TIME NOT NULL,
    frequency TEXT DEFAULT 'Daily' CHECK (frequency IN ('Daily', 'Once', 'Hourly', 'Weekly')),
    done BOOLEAN DEFAULT FALSE,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. COGNITIVE SESSIONS (AI/ML Telemetry & DDA Tracking)
CREATE TABLE IF NOT EXISTS public.cognitive_sessions (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    game_type TEXT NOT NULL CHECK (game_type IN ('sequence_memory', 'general_knowledge', 'odd_one_out', 'task_sequencing')),
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 10),
    score INTEGER NOT NULL,
    accuracy NUMERIC(4, 2) NOT NULL CHECK (accuracy BETWEEN 0.0 AND 1.0),
    reaction_time_ms INTEGER NOT NULL, -- In milliseconds for cognitive latency analysis
    mistake_count INTEGER DEFAULT 0,
    session_metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_patients_caregiver ON public.patients(caregiver_id);
CREATE INDEX IF NOT EXISTS idx_memories_patient ON public.memories(patient_id);
CREATE INDEX IF NOT EXISTS idx_tasks_patient_date ON public.tasks(patient_id, date);
CREATE INDEX IF NOT EXISTS idx_reminders_patient ON public.reminders(patient_id);
CREATE INDEX IF NOT EXISTS idx_cog_patient_time ON public.cognitive_sessions(patient_id, created_at DESC);

-- =========================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =========================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cognitive_sessions ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can view and update their own profile
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Patients: Caregivers can manage their assigned patients
CREATE POLICY "Caregivers can view assigned patients" ON public.patients
    FOR SELECT USING (caregiver_id = auth.uid());

CREATE POLICY "Caregivers can insert assigned patients" ON public.patients
    FOR INSERT WITH CHECK (caregiver_id = auth.uid());

CREATE POLICY "Caregivers can update assigned patients" ON public.patients
    FOR UPDATE USING (caregiver_id = auth.uid());

-- Memories: Accessible if patient belongs to caregiver
CREATE POLICY "Caregiver manage patient memories" ON public.memories
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients 
            WHERE patients.id = memories.patient_id 
            AND patients.caregiver_id = auth.uid()
        )
    );

-- Tasks: Accessible if patient belongs to caregiver
CREATE POLICY "Caregiver manage patient tasks" ON public.tasks
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients 
            WHERE patients.id = tasks.patient_id 
            AND patients.caregiver_id = auth.uid()
        )
    );

-- Reminders: Accessible if patient belongs to caregiver
CREATE POLICY "Caregiver manage patient reminders" ON public.reminders
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients 
            WHERE patients.id = reminders.patient_id 
            AND patients.caregiver_id = auth.uid()
        )
    );

-- Cognitive Sessions: Accessible if patient belongs to caregiver
CREATE POLICY "Caregiver view patient cognitive telemetry" ON public.cognitive_sessions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.patients 
            WHERE patients.id = cognitive_sessions.patient_id 
            AND patients.caregiver_id = auth.uid()
        )
    );
