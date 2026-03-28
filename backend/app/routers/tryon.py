"""
Virtual Try-On API endpoints for pose detection and clothing overlay.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user
from app.services.tryon_service import TryOnService
from app.services import catalog_store_db

router = APIRouter(tags=["try-on"])

# Global instance of TryOnService (initialize once)
tryon_service = TryOnService()


@router.post("/preview")
async def preview_try_on(
    user_photo: UploadFile = File(...),
    clothing_photo: UploadFile = File(...),
    clothing_type: str = Form(default="top"),
    current_user=Depends(get_current_user)
):
    """
    Preview try-on with direct clothing image upload (no product lookup).
    
    Returns:
        {
            "success": bool,
            "image": "base64_encoded_result",
            "message": str,
            "clothing_type": str
        }
    """
    try:
        # Read file contents
        user_image_bytes = await user_photo.read()
        clothing_image_bytes = await clothing_photo.read()
        
        # Validate clothing_type
        if clothing_type not in ["top", "bottom", "shoes"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid clothing_type. Must be 'top', 'bottom', or 'shoes'"
            )
        
        # Process try-on
        result_base64, success = tryon_service.overlay_clothing(
            user_image_bytes,
            clothing_image_bytes,
            clothing_type
        )
        
        if not success:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Человек не обнаружен на фото. Пожалуйста, загрузите фото где видна ваша фигура.",
                    "image": None,
                    "clothing_type": clothing_type
                }
            )
        
        return {
            "success": True,
            "image": result_base64,
            "message": "Try-on успешно создана",
            "clothing_type": clothing_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Ошибка при обработке: {str(e)}",
                "image": None
            }
        )


@router.post("/upload")
async def upload_try_on(
    user_photo: UploadFile = File(...),
    product_id: int = Form(...),
    clothing_type: str = Form(default="top"),
    current_user=Depends(get_current_user)
):
    """
    Try-on with product image lookup from catalog.
    
    Args:
        user_photo: User's photo file
        product_id: Product ID from catalog
        clothing_type: Type of clothing ("top", "bottom", "shoes")
    
    Returns:
        {
            "success": bool,
            "image": "base64_encoded_result",
            "product_id": int,
            "product_name": str,
            "message": str
        }
    """
    try:
        # Get product from database
        product = await catalog_store_db.get_product(product_id)
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {product_id} not found"
            )
        
        # Check if product has images
        if not product.get("images") or len(product.get("images", [])) == 0:
            raise HTTPException(
                status_code=400,
                detail="Product has no images"
            )
        
        # Read user photo
        user_image_bytes = await user_photo.read()
        
        # Get product image bytes
        # If image is stored as URL path, we need to read it from file system
        clothing_image_bytes = await _get_product_image_bytes(product["images"][0])
        
        if not clothing_image_bytes:
            raise HTTPException(
                status_code=500,
                detail="Could not load product image"
            )
        
        # Validate clothing_type
        if clothing_type not in ["top", "bottom", "shoes"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid clothing_type. Must be 'top', 'bottom', or 'shoes'"
            )
        
        # Process try-on
        result_base64, success = tryon_service.overlay_clothing(
            user_image_bytes,
            clothing_image_bytes,
            clothing_type
        )
        
        if not success:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Человек не обнаружен на фото. Пожалуйста, загрузите фото где видна ваша фигура.",
                    "image": None,
                    "product_id": product_id,
                    "product_name": product.get("name")
                }
            )
        
        return {
            "success": True,
            "image": result_base64,
            "product_id": product_id,
            "product_name": product.get("name"),
            "message": "Try-on успешно создана"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Ошибка при обработке: {str(e)}",
                "image": None
            }
        )


async def _get_product_image_bytes(image_path: str) -> bytes:
    """
    Get product image bytes from file path.
    
    Args:
        image_path: Path to image (e.g., "/static/images/product_7_123456_user.jpg")
    
    Returns:
        Image bytes or None if file not found
    """
    try:
        from pathlib import Path
        from urllib.parse import urlparse

        if not image_path:
            return None

        # tryon.py -> routers -> app -> backend
        backend_dir = Path(__file__).resolve().parents[2]
        static_dir = (backend_dir / "static").resolve()

        # Handle full URL, absolute path, and relative path
        parsed = urlparse(image_path)
        normalized_path = parsed.path if parsed.scheme else image_path
        normalized_path = normalized_path.lstrip("/")

        if normalized_path.startswith("static/"):
            candidate = (backend_dir / normalized_path).resolve()
        elif normalized_path.startswith("images/"):
            candidate = (static_dir / normalized_path).resolve()
        else:
            # Fallback for plain filenames or other relative paths
            candidate = (static_dir / normalized_path).resolve()

        # Security check: allow only files under backend/static
        if static_dir not in candidate.parents and candidate != static_dir:
            raise ValueError("Invalid image path")

        if candidate.exists() and candidate.is_file():
            with open(candidate, "rb") as f:
                return f.read()
        else:
            print(f"Image file not found: {candidate}")
            return None
            
    except Exception as e:
        print(f"Error reading product image: {str(e)}")
        return None
