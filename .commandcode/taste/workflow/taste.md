# Workflow Preferences

- Works on Windows (cmd/PowerShell) with Node 24, npm 11, and Python 3.12 via the `py` launcher; Python deps go in a project-level `venv`. Confidence: 0.8
- Full-stack monorepo workflow: FastAPI backend (port 8000), Vite/React frontend (port 3000), and Expo/React Native mobile (port 8081) all running simultaneously in development. Confidence: 0.8
- For "get it running" tasks, expects the agent to take full end-to-end ownership — install all requirements, create `.env` files from examples, start every dev server, and verify health — without pausing for step-by-step approval. Confidence: 0.75
- Values cross-platform consistency: wants user-facing settings (e.g. language) to be a single source of truth shared across mobile, web, and backend rather than diverging per platform. Confidence: 0.6
- When asked for feature or design suggestions ("suggest changes"), expects the agent to inspect the actual implementation/current codebase first and ground recommendations in it rather than give generic advice. Confidence: 0.7
- Prefers implementation to be broken down and executed "task by task" — a todo list spanning backend → frontend → mobile, checking off each item as it's completed rather than one big unstructured change. Confidence: 0.7
- Expects "100% production grade code": add/update tests, run the test suite, and verify the build/parse before declaring the work done. Confidence: 0.8
- Wants patient-facing UI fully localized across all supported languages; treats English-only pages in an otherwise localized app as a gap to close rather than acceptable partial i18n. Confidence: 0.7
