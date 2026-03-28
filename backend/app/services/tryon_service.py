"""
Virtual Try-On Service using MediaPipe and OpenCV for pose detection and clothing overlay.
"""

import cv2
import numpy as np
from io import BytesIO
import base64
from typing import Optional, Tuple, Dict
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class TryOnService:
    """Service for virtual try-on functionality using pose detection and clothing overlay."""
    
    def __init__(self):
        """Initialize MediaPipe solutions for pose and selfie segmentation."""
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
            from mediapipe import Image as MPImage
            
            self.vision = vision
            self.MPImage = MPImage
            self.mp_python = mp_python
            logger.info("MediaPipe initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe: {e}")
            raise
    
    def overlay_clothing(
        self,
        user_image_bytes: bytes,
        clothing_image_bytes: bytes,
        clothing_type: str = "top"
    ) -> Tuple[str, bool]:
        """
        Overlay clothing on user image using simple image blending.
        
        Args:
            user_image_bytes: User photo as bytes
            clothing_image_bytes: Clothing product image as bytes
            clothing_type: Type of clothing ("top", "bottom", "shoes")
        
        Returns:
            Tuple[base64_result, success]: Base64 encoded result image and success flag
        """
        try:
            # Load images
            user_image = self._load_image(user_image_bytes)
            clothing_image = self._load_image(clothing_image_bytes)
            
            if user_image is None or clothing_image is None:
                logger.warning("Failed to load one or both images")
                return "", False
            
            # Simple overlay: resize clothing to fit upper region and blend
            h_user, w_user = user_image.shape[:2]
            
            # Resize clothing image to match user image width
            h_clothing, w_clothing = clothing_image.shape[:2]
            aspect_ratio = w_clothing / h_clothing
            new_width = int(w_user * 0.8)  # 80% of user image width
            new_height = int(new_width / aspect_ratio)
            
            clothing_resized = cv2.resize(clothing_image, (new_width, new_height))
            
            # Create result image by copying user image
            result_image = user_image.copy()
            
            # Position for overlay (center horizontally, upper part vertically)
            x_offset = (w_user - new_width) // 2
            y_offset = int(h_user * 0.15)  # Start at 15% from top
            
            # Ensure we don't go out of bounds
            if y_offset + new_height > h_user:
                new_height = h_user - y_offset
                clothing_resized = clothing_resized[:new_height, :]
            
            if x_offset + new_width > w_user:
                new_width = w_user - x_offset
                clothing_resized = clothing_resized[:, :new_width]
            
            # Simple alpha blending
            if clothing_resized.shape[2] == 4:  # RGBA
                alpha = clothing_resized[:, :, 3:4] / 255.0
                clothing_rgb = clothing_resized[:, :, :3]
            else:
                alpha = np.ones((clothing_resized.shape[0], clothing_resized.shape[1], 1))
                clothing_rgb = clothing_resized
            
            # Blend
            end_x = min(x_offset + clothing_rgb.shape[1], w_user)
            end_y = min(y_offset + clothing_rgb.shape[0], h_user)
            
            result_region = result_image[y_offset:end_y, x_offset:end_x]
            clothing_region = clothing_rgb[:end_y - y_offset, :end_x - x_offset]
            alpha_region = alpha[:end_y - y_offset, :end_x - x_offset]
            
            # Alpha blend
            result_image[y_offset:end_y, x_offset:end_x] = (
                clothing_region * alpha_region + result_region * (1 - alpha_region)
            ).astype(np.uint8)
            
            # Convert to base64
            result_base64 = self._image_to_base64(result_image)
            
            logger.info(f"Successfully overlaid {clothing_type} clothing")
            return result_base64, True
            
        except Exception as e:
            logger.error(f"Error in overlay_clothing: {str(e)}")
            return "", False
    
    def _load_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Load image from bytes."""
        try:
            image = Image.open(BytesIO(image_bytes))
            image = image.convert("RGB")
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            return image_cv
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return None
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert image to base64 string."""
        try:
            _, buffer = cv2.imencode('.jpg', image)
            image_bytes = buffer.tobytes()
            base64_str = base64.b64encode(image_bytes).decode('utf-8')
            return base64_str
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            return ""

