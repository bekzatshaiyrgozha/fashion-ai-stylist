"""Try-on service stub: compose user image with garment assets.

This module will likely use OpenCV / Mediapipe / Pillow to perform
segmentation, pose estimation, and composition for virtual try-on.
"""

from typing import Any


class TryOnService:
    """Service that applies a garment onto a user image.

    Implement the heavy image-processing logic here. Keep methods small
    and testable.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def apply_tryon(self, user_image_bytes: bytes, garment_asset: bytes) -> Any:
        """Return composed image bytes or metadata.

        Raise NotImplementedError until implemented.
        """
        raise NotImplementedError("Try-on logic not implemented")
