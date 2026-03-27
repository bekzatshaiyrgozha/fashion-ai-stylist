"""Pydantic models for API payloads.

Define request/response shapes used by routers and services.
"""

from pydantic import BaseModel
from typing import Optional, List


class OutfitRequest(BaseModel):
    """Request to generate an outfit.

    Expand fields with user preferences, size, occasion, and budget.
    """
    user_id: Optional[str]
    preferences: Optional[List[str]] = []
    size: Optional[str]


class TryOnRequest(BaseModel):
    """Request body for try-on endpoint (when not using multipart file)."""
    # Could include base64 image, or references to stored assets
    image_base64: Optional[str]
    garment_id: Optional[str]


class TryOnResponse(BaseModel):
    """Response for try-on requests.

    Typically contains a URL to the composed image or raw bytes encoded.
    """
    result_url: Optional[str]
    message: Optional[str]
