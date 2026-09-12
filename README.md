# MEMORA — AI-Based Cognitive & Daily-Life Assistance Platform
**Smart India Hackathon 2026 (Problem Statement ID: SIH26003)**  
*Team ID: 99 | Team Name: VERTEX*

---

## 🌟 Production Architecture Overview

MEMORA has been upgraded from a prototype script to a production-grade healthcare architecture:

- **Backend:** **FastAPI** (Asynchronous Python 3.11+, Pydantic v2 validation, WebSockets/REST, OpenAPI docs).
- **Database & Auth:** **Supabase** (PostgreSQL with Row-Level Security, GoTrue Auth, CDN Storage for memory photos).
- **Frontend:** **React 18** (Vite, Tailwind CSS, Lucide icons, accessible elder-friendly UI with high touch-targets).
- **Voice & Regional AI:** **Sarvam AI** (Indian regional speech-to-text `saaras:v1` and text-to-speech `bulbul:v1` in Tamil, Hindi, Kannada, Telugu, English).
- **AI/ML Engine:** **Dynamic Difficulty Adjustment (DDA)** algorithm dynamically adapting sequence memory length and display times according to patient response latencies and accuracy.

---

## 📁 Repository Structure

```
MEMORA/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/routes/       # auth, patients, memories, routines, cognitive, voice, caregiver
│   │   ├── core/             # config.py, database.py, security.py
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # sarvam_service.py, dda_engine.py
│   │   └── main.py           # FastAPI entry point
│   ├── tests/                # Pytest test suite (DDA & API routes)
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment variable template
├── frontend/                 # React 18 Application (Vite + Tailwind)
│   ├── src/
│   │   ├── components/       # Sidebar, PinModal, VoiceAssistantModal
│   │   ├── pages/            # Today, Memories, Routine, Activities, Exercise, Sleep, Caregiver
│   │   ├── services/         # api.js client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── supabase/                 # Supabase PostgreSQL Database
│   ├── schema.sql            # Relational schema with RLS policies
│   └── seed.sql              # Initial seed data
└── app.py                    # Legacy Flask prototype (preserved)
```

---

## 🚀 Quickstart Guide

### 1. Database Setup (Supabase)
1. Log into your [Supabase Dashboard](https://supabase.com).
2. Create a new project.
3. Open the **SQL Editor** in Supabase and paste the contents of [`supabase/schema.sql`](supabase/schema.sql). Click **Run**.
4. (Optional) Run [`supabase/seed.sql`](supabase/seed.sql) to populate sample memory and routine data.
5. In Supabase **Storage**, create a public bucket named `patient-memories`.

---

### 2. Backend Setup (FastAPI)
1. Navigate to the backend directory and set up environment:
   ```bash
   cd backend
   py -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   copy .env.example .env
   ```
3. Run the FastAPI development server:
   ```bash
   py -m uvicorn app.main:app --reload --port 8000
   ```
4. Access the interactive Swagger API docs at:  
   👉 **http://localhost:8000/api/docs**

---

### 3. Frontend Setup (React + Vite)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open your browser at **http://localhost:3000**.

---

### 4. Running Backend Unit Tests
To verify the Dynamic Difficulty Adjustment (DDA) engine and FastAPI endpoints:
```bash
cd backend
py -m pytest tests/
```

---

## 🧠 AI Features Highlight (SIH26003)

1. **Dynamic Difficulty Adjustment (DDA):**
   - Automatically tracks reaction latency (ms) and error counts.
   - Adjusts stimulus presentation time (1.5s - 4.5s) and sequence complexity (3 - 6 symbols) to keep patients engaged without frustration.
2. **Sarvam AI Regional Voice:**
   - Accurate speech recognition for Indian accents and regional languages.
   - Elderly-friendly pacing (0.85x speed) using gentle voice models (`bulbul:v1`).
3. **Caregiver Cognitive Stability Index:**
   - Generates a clinical index (0-100) based on response time variance and recall consistency for attending neurologists.
