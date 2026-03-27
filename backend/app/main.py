"""Main FastAPI application for Fashion AI Stylist.

This module wires routers, middleware (CORS), and health checks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers (implementations in app/routers)
from app.routers import outfit, tryon

app = FastAPI(title="Fashion AI Stylist API")

# NOTE: In production restrict origins appropriately
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(outfit.router, prefix="/outfit", tags=["outfit"])
app.include_router(tryon.router, prefix="/tryon", tags=["tryon"])


@app.get("/health")
async def health_check():
    """Simple health check endpoint.

    Return a minimal status object for readiness/liveness checks.
    """
    return {"status": "ok"}

# Additional startup/shutdown events, logging, and dependency wiring
# can be added here.
