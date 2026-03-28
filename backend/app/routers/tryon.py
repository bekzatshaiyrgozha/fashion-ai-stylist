"""
Virtual Try-On API endpoints for pose detection and clothing overlay.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import verify_token
from app.db.db_config import async_session_maker
from app.services.tryon_service import TryOnService
from app.services import catalog_store_db

router = APIRouter(prefix="/tryon", tags=["try-on"])

# Global instance of TryOnService (initialize once)
tryon_service = TryOnService()


@router.post("/preview")
async def preview_try_on(
    user_photo: UploadFile = File(...),
    clothing_photo: UploadFile = File(...),
    clothing_type: str = Form(default="top"),
    user_payload: dict = Depends(verify_token)
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
    user_payload: dict = Depends(verify_token)
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
        if not product.images or len(product.images) == 0:
            raise HTTPException(
                status_code=400,
                detail="Product has no images"
            )
        
        # Read user photo
        user_image_bytes = await user_photo.read()
        
        # Get product image bytes
        # If image is stored as URL path, we need to read it from file system
        clothing_image_bytes = await _get_product_image_bytes(product.images[0])
        
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
                    "product_name": product.name
                }
            )
        
        return {
            "success": True,
            "image": result_base64,
            "product_id": product_id,
            "product_name": product.name,
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
        import os
        
        # Convert path to absolute file system path
        # Image paths are stored as /static/images/...
        # Files are actually in backend/static/images/...
        
        if image_path.startswith("/"):
            image_path = image_path[1:]  # Remove leading slash
        
        # Get the backend directory (parent of app directory)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(backend_dir, image_path)
        
        # Security check: ensure path is within static directory
        static_dir = os.path.join(backend_dir, "static")
        if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
            raise ValueError("Invalid image path")
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        else:
            print(f"Image file not found: {file_path}")
            return None
            
    except Exception as e:
        print(f"Error reading product image: {str(e)}")
        return None
