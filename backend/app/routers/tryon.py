"""Router for virtual try-on endpoints.

Endpoints here should accept user images and garment assets and return
a composed try-on result or job status.
"""

from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Try-on router - add endpoints here"}


@router.post("/apply")
async def apply_tryon(image: UploadFile = File(...)):
    # TODO: validate input, pass bytes to app.services.tryon_service.TryOnService
    return {"message": "Try-on apply - not implemented"}
