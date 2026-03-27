# Fashion AI Stylist

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

🚀 Professional AI Stylist & Virtual Try-On for fashion marketplaces

## Overview

Fashion AI Stylist is an MVP backend for an AI-powered styling assistant and virtual try-on system built during the FashionMode Hackathon (Karaganda, 2026). The system generates stylish outfits from a marketplace catalog and provides a 2D Virtual Try-On experience that overlays garments on a user's photo.

Key capabilities:
- AI-powered outfit generation that composes complete looks from catalogue items.
- 2D Virtual Try-On using computer-vision tools (MediaPipe/OpenCV) to overlay garments on user images.

## Features

- 👗 Outfit generation by style (casual, sport, office)
- 🎨 Color compatibility handling and style-aware matching
- 📸 Virtual Try-On (2D overlay using MediaPipe + OpenCV)
- 🔐 JWT-based authentication for secure endpoints
- 🛠️ Full Admin Panel: CRUD for products, categories, and users
- 📦 REST API implemented with FastAPI

## Tech Stack

```
Backend:  FastAPI, SQLAlchemy, PostgreSQL, JWT
AI/ML:    Sentence Transformers, FAISS, Anthropic Claude API
CV:       MediaPipe, OpenCV, Pillow
Testing:  Pytest, HTTPX
```

## Repository Structure

```
fashion-ai-stylist/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── categories.py
│   │   │   ├── outfit.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── outfit_generator.py
│   │   │   └── tryon_service.py
│   │   └── schemas/
│   │       └── models.py
│   ├── tests/
│   └── requirements.txt
└── frontend/
```

## Getting Started

Follow these steps to run the backend locally.

```bash
# Clone repository
git clone https://github.com/username/fashion-ai-stylist.git
cd fashion-ai-stylist/backend

# Create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy example env and adjust if needed
cp .env.example .env

# Run the development server
uvicorn app.main:app --reload
```

API docs will be available at `http://localhost:8000/docs`.

## Environment Variables (.env.example)

```env
DATABASE_URL=postgresql://user:password@localhost/fashiondb
SECRET_KEY=your_secret_key
ANTHROPIC_API_KEY=your_api_key
```

## API Endpoints (Short Reference)

| Method | URL | Description |
|--------|-----|-------------|
| POST | /auth/register | Register a new user |
| POST | /auth/login | Authenticate and receive token |
| GET  | /products/ | List all products |
| POST | /outfit/generate | Generate an outfit based on preferences |
| POST | /tryon/upload | Upload image for Virtual Try-On |
| GET  | /admin/stats/ | Admin dashboard statistics |

Refer to the OpenAPI docs (`/docs`) for full request/response schemas.

## Testing

Run the test suite with Pytest (uses HTTPX AsyncClient and an in-memory SQLite for CI):

```bash
cd backend
pytest tests/ -v
```

## Team & Event

- Hackathon: FashionMode Hackathon — Karaganda, 2026
- Organizers: Digital Department of Karaganda Region, Terricon Valley, AVISHU
- Case: AI Stylist & Virtual Try-On for fashion marketplaces

## License

This project is released under the MIT License. See the `LICENSE` file for details.

---

If you'd like, I can also:
- add a `Dockerfile` + `docker-compose.yml` example for local development
- add CI workflow (GitHub Actions) to run tests on push/PR

Good luck with the hackathon — make it stylish! ✨
