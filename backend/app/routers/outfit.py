"""Router for outfit-related endpoints.

Add endpoints to generate and retrieve outfit recommendations.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Outfit router - add endpoints here"}


@router.post("/generate")
async def generate_outfit():
    # TODO: accept a request schema from app.schemas.models
    # TODO: call outfit generation logic from app.services.outfit_generator
    return {"message": "Generate outfit - not implemented"}
