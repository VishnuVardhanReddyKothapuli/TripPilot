# Deployment Guide

This guide covers deploying TripPilot AI to modern PaaS platforms like Render and Railway.

## Before deployment

This application has one shared owner workspace, protected by a random SECRET_KEY. It does not provide separate user accounts. Set FRONTEND_URL to the exact HTTPS frontend origin. Set NEXT_PUBLIC_API_URL before building the frontend (changing it requires rebuilding). Never expose Ollama publicly without network access controls. Configure a reverse proxy with request/rate limits for public deployments. Existing database schema changes require migrations; automatic table creation only initializes missing tables.

## Deploying to Render

We have provided a `render.yaml` configuration file for deploying to Render using Blueprint.

1. Create a free account on [Render](https://render.com/).
2. Go to the Render Dashboard and click **New > Blueprint**.
3. Connect your GitHub repository containing the TripPilot AI code.
4. Render will automatically detect the `render.yaml` file and provision the following resources:
   - A PostgreSQL 16 database.
   - A Web Service for the FastAPI backend.
   - A Web Service for the Next.js frontend.
5. Environment variables will be automatically set up between the services, and a secure `SECRET_KEY` will be generated.
6. **Note**: You will need to host Ollama separately (using a private, authenticated network) as Render's free tier is not suited for running large LLMs directly. Update the `OLLAMA_BASE_URL` in the Render dashboard if you host Ollama externally, Only Ollama is implemented; other provider values disable model planning.

## Deploying to Railway

1. Create a free account on [Railway](https://railway.app/).
2. Click **New Project** and select **Deploy from GitHub repo**.
3. Railway will analyze your repository.
4. Add a **PostgreSQL** plugin to your project.
5. Create a service for the backend:
   - Set the root directory to `backend`.
   - Set the build command or Dockerfile path.
   - Expose port `8001`.
   - Map the `DATABASE_URL` variable to the PostgreSQL plugin.
6. Create a service for the frontend:
   - Set the root directory to `frontend`.
   - Set the build command or Dockerfile path.
   - Expose port `3000`.
   - Map `NEXT_PUBLIC_API_URL` to your backend service's public URL.
7. Manage your environment variables (like `LLM_PROVIDER`, `SECRET_KEY`, etc.) directly in the Railway dashboard.
