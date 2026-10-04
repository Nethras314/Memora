# Workflow Preferences

- Works on Windows (cmd/PowerShell) with Node 24, npm 11, and Python 3.12 via the `py` launcher; Python deps go in a project-level `venv`. Confidence: 0.8
- Full-stack monorepo workflow: FastAPI backend (port 8000), Vite/React frontend (port 3000), and Expo/React Native mobile (port 8081) all running simultaneously in development. Confidence: 0.8
- For "get it running" tasks, expects the agent to take full end-to-end ownership — install all requirements, create `.env` files from examples, start every dev server, and verify health — without pausing for step-by-step approval. Confidence: 0.75
- Values cross-platform consistency: wants user-facing settings (e.g. language) to be a single source of truth shared across mobile, web, and backend rather than diverging per platform. Confidence: 0.6
- When asked for feature or design suggestions ("suggest changes"), expects the agent to inspect the actual implementation/current codebase first and ground recommendations in it rather than give generic advice. Confidence: 0.7
- Prefers implementation to be broken down and executed "task by task" — a todo list spanning backend → frontend → mobile, checking off each item as it's completed rather than one big unstructured change. Confidence: 0.7
- Prefers a clean, from-scratch restart of the local dev stack: when asked to (re)start services, kill every running instance — including stale or duplicate dev servers holding a port — and launch each service fresh rather than reusing an already-running one. Confidence: 0.7
- Refers to the tiers by their deploy platform names and expects the agent to map them: "expo" = Expo/React Native mobile, "vercel" = Vite/React frontend, "render" = FastAPI backend — and to resolve ambiguity toward local dev servers, not cloud deploys. Confidence: 0.65
- Willing to throw away all local git state to match the remote: prefers a hard sync to `origin/main` (discarding uncommitted edits and divergent local commits) over reconciling or preserving local work, while still wanting untracked/deploy configs flagged before they're deleted. Confidence: 0.7
- Expects "100% production grade code": add/update tests, run the test suite, and verify the build/parse before declaring the work done. Confidence: 0.8
- Wants verified fixes committed and pushed directly to `main` (no feature branches/PRs) — when told to "push all code changes," commit the code and push without repeatedly asking for confirmation first. Confidence: 0.6
- Wants patient-facing UI fully localized across all supported languages; treats English-only pages in an otherwise localized app as a gap to close rather than acceptable partial i18n. Confidence: 0.7
- Prefers incremental, idempotent SQL migration deltas when schema changes ship: provide just the new statements to run in the Supabase SQL editor rather than expecting a re-run of the full migration file. Confidence: 0.7
- For feature-completeness / production-readiness audits, wants the actual code read fresh across the whole stack (backend, frontend, mobile, schema) rather than relying on an earlier report or summary — and each requirement verified against the implementation, not the README or feature claims. Confidence: 0.8
- Prefers lightweight, transparent, deterministic ML (e.g. scikit-learn online learning + Elo) over LLM-driven or opaque approaches for adaptive/personalization features. Confidence: 0.6
- Prefers full offline-first support — PWA/service worker on web plus local cache, write queue, and background sync on mobile — rather than cache-only or online-only. Confidence: 0.6
- Prefers real reminder/alert delivery via a server-side scheduler + push notifications, not on-device-only local notifications. Confidence: 0.6
- Keeps scope tight and defers optional additions (e.g. declined adding new regional languages) to focus on closing existing gaps first. Confidence: 0.65
