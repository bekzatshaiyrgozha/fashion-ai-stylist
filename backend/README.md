# Fashion AI Stylist — Backend

This is a starter FastAPI project scaffold for the FashionMode Hackathon (Kazakhstan, 2026).

Quick start

1. Create and activate a Python environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app (from the `backend/` directory):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Project layout

- `app/main.py`: FastAPI application and router wiring
- `app/routers/`: route modules (`outfit.py`, `tryon.py`)
- `app/services/`: business logic and image-processing services
- `app/schemas/models.py`: pydantic request/response models

Next steps

- Implement service logic in `app/services` using OpenCV / Mediapipe for try-on
- Add authentication, storage for assets, and model inference pipelines
- Add tests and CI

Docker (local)

1. Copy `.env.example` to `.env` and set values if needed:

```bash
cd backend
cp .env.example .env
```

2. Build and run services with Docker Compose:

```bash
docker compose up --build
```

3. Open http://localhost:8000 — FastAPI app will be available.

To run in background:

```bash
docker compose up -d --build
```

To stop and remove containers:

```bash
docker compose down
```

