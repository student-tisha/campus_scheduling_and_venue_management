# Deploy the backend (Render + free PostgreSQL)

Why PostgreSQL: free hosts wipe local files when they restart, which would erase the timetable. A hosted database keeps it.

## 1. Database (Neon)
1. Create a free project at neon.tech and copy the connection string.
2. Change its start from `postgresql://` to `postgresql+psycopg2://` and keep `?sslmode=require` at the end.

## 2. Web service (Render)
1. New, then Web Service, then connect the GitHub repo.
2. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements-prod.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment variables:
   - `DATABASE_URL` = the Neon string from step 1
   - `SECRET_KEY` = any long random text
   - `FRONTEND_ORIGIN` = your Vercel link (several links can be separated by commas)
   - `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (same as `.env.example`)
   - `PYTHON_VERSION` = `3.12.7` (if the build fails on the Python version, or OR-Tools has no build for your default)
4. Deploy. Open `<your-render-link>/api/health` to check.

## 3. After deploying
- Log in as admin and run `POST /api/admin/generate` once so the app has a timetable.
- Free Render services sleep after a while. Open the link a few minutes before judging.
- In the frontend host, set `VITE_API_URL` to the Render link.
- Do not push or redeploy after the submission deadline.
