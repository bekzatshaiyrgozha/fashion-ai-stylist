# Virtual Try-On Feature - Implementation Guide

## Overview
The Virtual Try-On feature provides users with an AI-powered way to visualize clothing items on their own photos using MediaPipe pose detection and OpenCV image processing.

## Architecture

### Backend Components

#### 1. **TryOn Service** (`backend/app/services/tryon_service.py`)
Core service handling pose detection and clothing overlay:

**Key Features:**
- **MediaPipe Pose Detection**: Detects 33 body landmarks (shoulders, hips, knees, ankles, etc.)
- **Selfie Segmentation**: Creates binary mask of human body
- **Clothing Region Calculation**: Maps pose keypoints to clothing types:
  - `top`: Uses shoulders and hips for upper body garments
  - `bottom`: Uses hips and ankles for lower body garments
  - `shoes`: Uses ankle keypoints with downward extension

**Main Methods:**
```python
overlay_clothing(user_image_bytes, clothing_image_bytes, clothing_type)
  → Returns: (base64_result, success_flag)
```

**Image Processing Pipeline:**
1. Load user photo and clothing image from bytes
2. Detect pose landmarks with MediaPipe (returns 33 keypoints)
3. Get body segmentation mask for transparency blending
4. Calculate bounding box for target clothing region
5. Resize clothing image to fit region
6. Blend clothing with alpha transparency
7. Return base64-encoded result

**Error Handling:**
- Returns `False` if no human pose detected
- Gracefully handles missing landmarks
- Safe file I/O with try-catch blocks

---

#### 2. **TryOn Router** (`backend/app/routers/tryon.py`)
Exposes two API endpoints:

##### `/tryon/upload` - Product-based Try-On
```http
POST /tryon/upload
Content-Type: multipart/form-data

Parameters:
  - user_photo: File (JPEG/PNG)
  - product_id: Integer (from product catalog)
  - clothing_type: String (top|bottom|shoes)

Response (200 OK):
{
  "success": true,
  "image": "base64_encoded_jpg",
  "product_id": 7,
  "product_name": "Blue Shirt",
  "message": "Try-on успешно создана"
}

Error Response (400):
{
  "success": false,
  "message": "Человек не обнаружен на фото..."
}
```

**Workflow:**
1. Verify user is authenticated (httpOnly cookie)
2. Look up product by ID from PostgreSQL database
3. Read product image from `/static/images/` directory
4. Call TryOnService.overlay_clothing()
5. Return result as base64 + product metadata

##### `/tryon/preview` - Free Try-On
```http
POST /tryon/preview
Content-Type: multipart/form-data

Parameters:
  - user_photo: File (JPEG/PNG)
  - clothing_photo: File (JPEG/PNG)
  - clothing_type: String (top|bottom|shoes)

Response (200 OK):
{
  "success": true,
  "image": "base64_encoded_jpg",
  "clothing_type": "top",
  "message": "Try-on успешно создана"
}
```

**Workflow:**
1. Verify user is authenticated
2. Read both photos from uploaded files
3. Call TryOnService.overlay_clothing()
4. Return result without product context

---

### Frontend Components

#### 1. **TryOnModal Component** (`frontend/src/components/TryOnModal.jsx`)
React modal for try-on interaction:

**Props:**
```javascript
{
  isOpen: boolean,                          // Modal visibility
  onClose: () => void,                      // Close handler
  product: { id, name, ... },              // Product object
  onSuccess: (result) => void,             // Success callback
  userId: string                           // Current user ID
}
```

**Features:**
- **Dual Mode Upload:**
  - File upload with drag-and-drop UI
  - Camera capture with real-time video preview
  - File preview before processing

- **Clothing Type Selection:**
  ```javascript
  <select>
    <option value="top">Верх (рубашка, свитер)</option>
    <option value="bottom">Низ (штаны, юбка)</option>
    <option value="shoes">Обувь</option>
  </select>
  ```

- **State Management:**
  - `loading`: Processing state with spinner
  - `error`: Error message display
  - `resultImage`: Base64 result display
  - `uploadMode`: "upload" vs "camera"
  - `cameraStream`: MediaStream object for video

- **Camera Handling:**
  ```javascript
  navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } })
  ```
  - Requests user permission
  - Displays live video feed
  - Canvas capture on button click
  - Automatic cleanup on unmount

#### 2. **TryOnModal Styles** (`frontend/src/styles/TryOnModal.css`)
Professional modal UI with:
- Glassmorphism backdrop (blur effect)
- Smooth animations (slideUp on open)
- Responsive design (works on mobile)
- Color scheme matches brand (#ff6b6b primary)
- Accessibility (button states, error styling)

**Key CSS Classes:**
- `.modal-overlay`: Fixed position backdrop with blur
- `.modal-content`: Main modal container
- `.upload-area`: Dashed border file upload
- `.camera-area`: Video preview container
- `.result-section`: Try-on result display
- `.btn-primary/.btn-secondary`: Styled buttons

---

### Integration Points

#### 1. **Products Page** (`frontend/src/pages/Products.jsx`)
ProductCard component updated:
```javascript
<button onClick={() => setShowTryOn(true)}>
  🎨 Try On
</button>

<TryOnModal
  isOpen={showTryOn}
  onClose={() => setShowTryOn(false)}
  product={product}
/>
```

#### 2. **Product Detail Page** (`frontend/src/pages/Products.jsx`)
ProductDetailPage component updated:
```javascript
<button onClick={() => setShowTryOn(true)}>
  🎨 Try This On
</button>

<TryOnModal
  isOpen={showTryOn}
  onClose={() => setShowTryOn(false)}
  product={product}
/>
```

---

## API Flow Diagram

```
User Action
    ↓
Click "Try On" Button
    ↓
TryOnModal Opens
    ↓
User Uploads Photo / Captures from Camera
    ↓
Select Clothing Type (top/bottom/shoes)
    ↓
Click "🎨 Примерить"
    ↓
FormData sent to /tryon/upload
    ├─ user_photo (multipart file)
    ├─ product_id (from product object)
    └─ clothing_type (selected option)
    ↓
Backend:
  1. Verify authentication via httpOnly cookie
  2. Load product from database
  3. Read product image from /static/images/
  4. Load user photo from request
  5. TryOnService.overlay_clothing():
     - Load images with PIL
     - Detect pose with MediaPipe
     - Get body segmentation mask
     - Calculate clothing region from keypoints
     - Blend images with alpha transparency
     - Convert result to base64 JPEG
  6. Return { success: true, image: "base64..." }
    ↓
Frontend:
  1. Display base64 image in modal
  2. Show success message
  3. User can download or try another product
```

---

## Data Flow

### Pose Keypoint Mapping

MediaPipe provides 33 landmarks for full body:
```
Index  Name              Position
11     LEFT_SHOULDER     Upper left torso
12     RIGHT_SHOULDER    Upper right torso
23     LEFT_HIP          Lower left torso
24     RIGHT_HIP         Lower right torso
25     LEFT_KNEE         Upper left leg
26     RIGHT_KNEE        Upper right leg
27     LEFT_ANKLE        Lower left leg
28     RIGHT_ANKLE       Lower right leg
```

**For TOP clothing:**
- Bounding box: Between shoulders (top) and hips (bottom)
- Width: Shoulder-to-shoulder distance + padding
- Applies alpha blending for transparency

**For BOTTOM clothing:**
- Bounding box: Between hips (top) and ankles (bottom)
- Width: Hip-to-hip distance + padding
- Applies alpha blending

**For SHOES:**
- Bounding box: Ankle region extended downward
- Height: ~8% of image height
- Position: Centered on ankles

---

## Error Handling

### Backend Errors

| Error | HTTP | Message | Cause |
|-------|------|---------|-------|
| No pose detected | 400 | "Человек не обнаружен на фото..." | User photo doesn't show full body or face |
| Invalid clothing_type | 400 | "Invalid clothing_type. Must be..." | Sent value not in ["top", "bottom", "shoes"] |
| Product not found | 404 | "Product with id X not found" | product_id doesn't exist in DB |
| Product has no images | 400 | "Product has no images" | Product created without photo |
| Image processing error | 500 | "Ошибка при обработке: ..." | OpenCV/MediaPipe failure |

### Frontend Errors
- Camera permission denied: "Не удалось получить доступ к камере"
- No file selected: "Пожалуйста, выберите или сделайте фото"
- Network error: Retry with error message display

---

## Dependencies

### Backend (Python)
```
mediapipe==0.10.33          # Pose detection & body segmentation
opencv-python==4.9.0.80     # Image processing & overlay
pillow>=10.0.0              # Image loading & conversion
numpy                       # Array operations (via mediapipe)
fastapi                     # API framework
```

### Frontend (JavaScript)
```
react                       # Component library
native browser APIs:
  - navigator.mediaDevices.getUserMedia()  # Camera access
  - Canvas API                              # Image capture
  - Fetch API                               # HTTP requests
```

---

## Security Considerations

1. **Authentication**: All endpoints require valid httpOnly cookie
2. **File Validation**: 
   - Accept only JPEG/PNG files
   - Validate file size limits
   - Process in memory (no temp files)
3. **Path Traversal**: Image paths validated to stay within `/static/images/`
4. **CORS**: Only localhost:5173 allowed in development
5. **Input Validation**: clothing_type enum validation

---

## Performance Optimization

1. **MediaPipe Initialization**: Singleton instance in TryOnService (initialized once, reused for all requests)
2. **Image Compression**: Results saved as JPEG (not PNG) for smaller base64 strings
3. **Memory Management**: Temporary arrays released after processing
4. **Async Processing**: Backend handles image processing with minimal blocking

---

## Testing Checklist

### Backend Tests
- [ ] `/tryon/upload` with valid product_id
- [ ] `/tryon/upload` with invalid product_id (404)
- [ ] `/tryon/upload` with no person detected (400)
- [ ] `/tryon/preview` with two images
- [ ] Invalid clothing_type validation
- [ ] Unauthenticated request (should fail)
- [ ] Different pose angles (top-view, side, etc.)

### Frontend Tests
- [ ] Modal opens and closes correctly
- [ ] File upload triggers Try On request
- [ ] Camera button shows video feed
- [ ] Camera capture creates blob
- [ ] Clothing type selection works
- [ ] Result image displays
- [ ] Error messages appear on failure
- [ ] Mobile responsiveness

### Integration Tests
- [ ] Product detail page → Try On → Result display
- [ ] Products list → Product card → Try On modal
- [ ] Camera → Capture → Try On → Result
- [ ] Download result image
- [ ] Rapid successive requests don't crash backend

---

## Deployment

### Docker Setup
```bash
# Build image
docker build -t fashion-ai-tryon .

# Run with GPU support (optional)
docker run --gpus all -p 8000:8000 fashion-ai-tryon
```

### Environment Variables
```env
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/fashion_db
JWT_SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-key
```

### System Requirements
- **Memory**: 4GB+ RAM (MediaPipe + OpenCV intensive)
- **CPU**: Multi-core recommended for image processing
- **Disk**: 500MB+ for model cache

---

## Future Enhancements

1. **Multi-angle Preview**: Show clothing from multiple perspectives
2. **Color Customization**: Allow user to change clothing color before overlay
3. **Size Adjustment**: Scale clothing interactively
4. **Animation**: Clothing swap animation
5. **AR Integration**: Real-time phone camera preview
6. **Result Sharing**: Social media share buttons
7. **History**: Save user's previous try-ons
8. **Batch Processing**: Try-on for multiple clothing items

