# TripPilot AI

TripPilot AI is an intelligent travel planning assistant.

## Tech Stack
- **Frontend**: Next.js (Node.js)
- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16+
- **LLM**: Ollama (LLaMA 3.1)
- **External APIs**: Open-Meteo, Overpass (OSM), RestCountries, Wikivoyage and Wikipedia

## Prerequisites
- Docker & Docker Compose
- Node.js 22+ (for manual setup)
- Python 3.12+ (for manual setup)
- Ollama running locally (for LLM support)

## Quick Start
1. Copy `.env.example` to `.env` and adjust the variables:
   ```bash
   cp .env.example .env
   ```
2. Generate a key with `python -c "import secrets; print(secrets.token_urlsafe(32))"` and set `SECRET_KEY` in `.env`.
3. Start the services with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```
4. Access the app:
   - Frontend: http://localhost:3000
   - Open Settings and enter the server SECRET_KEY to access trips.
   - Backend API Docs: http://localhost:8001/docs

## Manual Setup Instructions

### Start this configured Windows workspace

Run `powershell -ExecutionPolicy Bypass -File .\start-local.ps1` from the project folder, then open http://localhost:3000. The launcher reuses the local PostgreSQL installation when `backend/.env` points to port 55432, and starts the API and frontend in the background. Logs are in `.local/`. Keep `.audit/postgres` because it contains the local database, including your saved trips.

Open Settings and paste `SECRET_KEY` from `backend/.env`. Never commit that file. This workspace's local database is separate from the `trippilot_audit` test database.

If Windows `npm` reports a missing `AppData/Roaming/npm/.../npm-cli.js`, invoke the installed CLI directly from `frontend`: `node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" ci --cache ../.npm-cache`. The launcher avoids this broken global npm shim.

### Backend
1. Navigate to the backend directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy the root `.env.example` to `backend/.env`, set the PostgreSQL URL and a random `SECRET_KEY` of at least 32 characters.
6. Run the server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8001`

### Frontend
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm ci`
3. Run the development server: `npm run dev`

## Environment Variables Documentation
- `APP_ENV`: Application environment (development/production).
- `DATABASE_URL`: Connection string for PostgreSQL.
- `LLM_PROVIDER`: The LLM service provider (e.g., ollama).
- `OLLAMA_BASE_URL`: The URL for the Ollama service.
- `OLLAMA_MODEL`: The LLM model to use (e.g., llama3.2:latest).
- `FRONTEND_URL`: URL of the frontend app.
- `CORS_ORIGINS`: Optional extra exact browser origins, comma-separated. Development accepts localhost, 127.0.0.1 and [::1] on the configured frontend port; other ports must be listed explicitly. Rebuild/recreate the backend container after changing CORS settings.
- `BACKEND_URL`: URL of the backend API.
- `SECRET_KEY`: Required bearer access key (at least 32 random characters). All API routes fail closed until configured. Never put this in a NEXT_PUBLIC variable.
- `NEXT_PUBLIC_API_URL`: Backend URL embedded at frontend build time; defaults to http://localhost:8001.

## API Overview
The backend provides endpoints for processing travel-related queries, generating itineraries, and interacting with external geospatial and weather APIs. For full API documentation, visit `/docs` on the running backend server.

## Deployment Guide
See [deployment.md](./deployment.md) for detailed deployment instructions on Render and Railway.

## Access and planning behavior

This is a private, single-owner workspace. Anyone with its access key can access all trips. Settings keeps the key in session storage for the current tab. Use HTTPS outside localhost, and do not share the key as if it were an individual user login.

Ollama uses `llama3.2:latest`. Run `ollama pull llama3.2` if it is not installed. Generation falls back to estimated plans if the model is unavailable or returns an invalid plan. Natural-language modifications require Ollama and preserve the last successful itinerary on failure. Fallback prices are group estimates in USD, with no invented currency conversion. Intercity/flight fares are excluded. Weather only covers the provider's available forecast window.

Trips are limited to 30 days and 20 travelers. Planning runs time out after five minutes; interrupted runs become retryable after six minutes. Background work runs in the API process; server restarts interrupt it.

New plans research named sights, restaurant descriptions and local cuisine from public travel guides, with source links. Large-city guides include up to three district pages. The day-by-day plan is followed by a trip summary and a “What to eat & where” section. Use Regenerate on saved plans to fetch the new research. Missing coverage is disclosed; opening hours, menus, transfers and prices still need confirmation. Wikimedia excerpts retain source attribution and CC BY-SA credit.

## Checks

Frontend: `npm run lint`, `npm run typecheck`, `npm run build`, `npm audit`.
Backend: from `backend`, run `python -m unittest discover -s tests -v`.
Set `TEST_DATABASE_URL` to a disposable PostgreSQL database whose name ends in `_test` or `_audit` to run the database integration checks. Tests only remove the trips they create. Use `pip-audit -r backend/requirements.txt` to check Python dependencies.
# TripPilot
