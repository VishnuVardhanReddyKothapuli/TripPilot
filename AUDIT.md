# TripPilot audit — 4 October 2026

## Fixed

- Local startup was blocked by missing frontend packages, an unreachable PostgreSQL database, and an invalid access key. Installed the locked frontend dependencies, started the existing workspace-local PostgreSQL installation, created a separate `trippilot` database, and configured `backend/.env` with a random access key. No existing database was deleted.
- Added `start-local.ps1` and Windows startup instructions. It bypasses this machine's broken global npm shim and writes service logs to `.local/`.
- Editing trip details could resurrect an itinerary for the old destination or dates after generation failed. Completed runs are now marked superseded when the trip changes; their history is retained but cannot be used for recovery or modification. Empty PATCH requests preserve the current trip.
- Optional weather requests blocked the itinerary screen until they completed or timed out. Weather now loads independently, and planning-status errors are shown instead of silently ignored. Trip navigation resets planning state.
- Development and production builds now use separate output folders, preventing development startup from removing production build artifacts.

## Verification

- All 8 backend tests passed against real PostgreSQL, including authorization, request-size limits, persistence, validation, concurrent planning, failure recovery, and outdated-itinerary regression coverage.
- Frontend ESLint, TypeScript, and production build passed.
- `pip check` reported no broken requirements.
- Live API smoke check created and persisted a two-day Tokyo trip, started generation, and received a completed two-day estimated itinerary. This sample trip is retained for inspection.
- Browser checks confirmed the homepage, Settings authentication, saved-trip listing, and the generated itinerary with its group budget. No browser console errors were observed. Preview: `.local/itinerary-check.png`.

## Remaining limitations

- Ollama is unavailable locally. Estimated generation works; natural-language modifications require a running Ollama instance and the configured `llama3.2:latest` model. Successful model-driven modification was not verified.
- npm's production dependency audit reported 5 high-severity entries through `braces`, `chokidar`, `micromatch`, `fast-glob`, and Tailwind 3. The suggested repair requires a breaking Tailwind 4 migration. No forced upgrade was applied. Advisory: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm
- Public geospatial/weather data availability and cloud/Docker deployment were not verified. The live generation check verifies graceful estimated output when integrations are unavailable.
- The local PostgreSQL installation lives in `.audit/postgres`; retain that folder to preserve saved trips. This setup is for local development. The app remains a single-owner workspace with a shared access key and in-process planning jobs.

## Run

From the project folder: `powershell -ExecutionPolicy Bypass -File .\start-local.ps1`.
Open http://localhost:3000 and enter the `SECRET_KEY` from `backend/.env` in Settings.
