# Virtual Try-On Integration Guide

## Quick Start

### Prerequisites
- Backend running on `localhost:8000`
- Frontend running on `localhost:5173`
- PostgreSQL database with products table populated

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
# Should include: mediapipe==0.10.33, opencv-python==4.9.0.80, pillow>=10.0.0
```

### Step 2: Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify with `curl http://localhost:8000/docs` → Should show Swagger UI with `/tryon/*` endpoints

### Step 3: Start Frontend

```bash
cd frontend
npm install
npm run dev
# Access at http://localhost:5173
```

### Step 4: Test Virtual Try-On

1. **Navigate to Products Page**
   - Click "Shop" in navigation

2. **Try-On a Product Card**
   - Click "🎨 Try On" button on any product
   - Modal opens with upload/camera options

3. **Upload a Photo**
   - Click "📤 Загрузить фото"
   - Select a photo showing your full body (head to feet)
   - Select clothing type (top/bottom/shoes)
   - Click "🎨 Примерить"
   - Wait for processing (2-5 seconds)
   - Result displays if pose detected

4. **Use Camera (Optional)**
   - Click "📷 Камера" tab
   - Click "🎥 Включить камеру"
   - Position yourself in frame (full body visible)
   - Click "📸 Сделать фото"
   - Camera switches to upload mode
   - Follow upload steps

---

## File Structure

### Backend Files Added/Modified

```
backend/
├── app/
│   ├── main.py                                  ← MODIFIED: Added tryon router import & registration
│   ├── routers/
│   │   ├── __init__.py                          ← MODIFIED: Added tryon export
│   │   └── tryon.py                             ← NEW: TryOn endpoints
│   └── services/
│       └── tryon_service.py                     ← NEW: MediaPipe + OpenCV logic
└── requirements.txt                             ← MODIFIED: Added mediapipe, opencv-python, pillow
```

### Frontend Files Added/Modified

```
frontend/
├── src/
│   ├── components/
│   │   └── TryOnModal.jsx                       ← NEW: TryOn UI component
│   ├── pages/
│   │   └── Products.jsx                         ← MODIFIED: Added Try-On buttons
│   └── styles/
│       └── TryOnModal.css                       ← NEW: Modal styling
└── .env                                          (Already configured with VITE_API_URL=/api)
```

---

## Database Schema (No Changes Required)

Existing `products` table is used:
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    category_id INTEGER,
    images TEXT[],                                -- Stores image URLs
    colors TEXT[],
    sizes TEXT[],
    style_tags TEXT[],
    scenarios TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

The `/tryon/upload` endpoint:
1. Queries by `product_id`
2. Reads image URL from `images[0]`
3. Loads image from `/static/images/` directory

---

## API Endpoints Reference

### POST /tryon/upload
**Try-On with product from catalog**

```bash
curl -X POST http://localhost:8000/tryon/upload \
  -H "Cookie: access_token=<YOUR_JWT_TOKEN>" \
  -F "user_photo=@/path/to/photo.jpg" \
  -F "product_id=7" \
  -F "clothing_type=top"
```

**Response (200 OK):**
```json
{
  "success": true,
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==",
  "product_id": 7,
  "product_name": "Blue Shirt",
  "message": "Try-on успешно создана"
}
```

**Response (400 - No Pose):**
```json
{
  "success": false,
  "message": "Человек не обнаружен на фото. Пожалуйста, загрузите фото где видна ваша фигура.",
  "image": null,
  "product_id": 7,
  "product_name": "Blue Shirt"
}
```

### POST /tryon/preview
**Try-On with any two images (no product lookup)**

```bash
curl -X POST http://localhost:8000/tryon/preview \
  -H "Cookie: access_token=<YOUR_JWT_TOKEN>" \
  -F "user_photo=@/path/to/person.jpg" \
  -F "clothing_photo=@/path/to/shirt.jpg" \
  -F "clothing_type=top"
```

---

## Frontend Integration Points

### Products.jsx Changes

**ProductCard Component:**
```javascript
// Added state
const [showTryOn, setShowTryOn] = useState(false);

// Added button in JSX
<button 
  className="btn btn-primary btn-block"
  onClick={() => setShowTryOn(true)}
  style={{ marginTop: '0.75rem' }}
>
  🎨 Try On
</button>

// Added modal
<TryOnModal
  isOpen={showTryOn}
  onClose={() => setShowTryOn(false)}
  product={product}
  onSuccess={() => console.log('Try-on completed')}
/>
```

**ProductDetailPage Component:**
```javascript
// Added in detail-section
<div className="detail-section">
  <button 
    className="btn btn-primary"
    onClick={() => setShowTryOn(true)}
    style={{ fontSize: '1.1rem', padding: '12px 24px' }}
  >
    🎨 Try This On
  </button>
</div>

<TryOnModal
  isOpen={showTryOn}
  onClose={() => setShowTryOn(false)}
  product={product}
/>
```

### TryOnModal Props

```javascript
<TryOnModal
  isOpen={boolean}              // Modal visibility
  onClose={() => {}}            // Close handler
  product={{                    // Product data
    id: 7,
    name: "Blue Shirt",
    price: 49.99,
    images: ["/static/images/..."],
    ...
  }}
  onSuccess={(result) => {}}    // Success callback
  userId={string}               // Optional: user ID
/>
```

---

## Error Handling

### Backend Errors

| Scenario | Status | Message |
|----------|--------|---------|
| No person in photo | 400 | "Человек не обнаружен на фото..." |
| Invalid clothing_type | 400 | "Invalid clothing_type. Must be 'top', 'bottom', or 'shoes'" |
| Product not found | 404 | "Product with id X not found" |
| Product has no images | 400 | "Product has no images" |
| Image load failure | 500 | "Ошибка при обработке: ..." |
| Unauthenticated | 401 | (Automatic redirect to login) |

### Frontend Error Handling

```javascript
// In TryOnModal.jsx
if (!response.ok) {
  const errorData = await response.json();
  throw new Error(errorData.message || "Ошибка при обработке изображения");
}

if (!result.success) {
  setError(result.message || "Try-on не удалась");
  return;
}
```

---

## Configuration

### Environment Variables

**Backend (.env)**
```env
DATABASE_URL=postgresql+asyncpg://user:password@host/database
JWT_SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-key
```

**Frontend (.env)**
```env
VITE_API_URL=/api
VITE_API_TIMEOUT=10000
```

### MediaPipe Settings (in tryon_service.py)

```python
self.pose = self.mp_pose.Pose(
    static_image_mode=True,        # Single image processing
    model_complexity=2,            # High accuracy (0, 1, or 2)
    smooth_landmarks=False         # No smoothing for static
)

self.selfie_segmentation = self.mp_selfie.SelfieSegmentation(
    model_selection=1              # Full body segmentation
)
```

### Clothing Region Padding (in tryon_service.py)

```python
# For top and bottom
padding = int((x_max - x_min) * 0.1)  # 10% padding

# For shoes
padding = int((x_max - x_min) * 0.2)  # 20% padding
```

---

## Performance Notes

### Image Processing Time
- **Pose Detection**: ~50-200ms (depends on image quality)
- **Segmentation**: ~50-100ms
- **Overlay**: ~30-50ms
- **Total**: ~150-350ms per try-on

### Memory Usage
- MediaPipe models: ~150MB (loaded once at startup)
- Per request: ~50-100MB (depends on image resolution)
- Recommended: 4GB+ RAM

### Optimization Tips
1. Resize images to max 1920x1440 to reduce processing time
2. Use JPEG format (smaller than PNG for base64)
3. Reuse TryOnService singleton instance (don't reinit)
4. Consider GPU acceleration for high-load deployment

---

## Testing Checklist

### Manual Tests
- [ ] Upload photo with person → Gets try-on result
- [ ] Upload blank photo → "Человек не обнаружен"
- [ ] Invalid product_id → 404 error
- [ ] Camera capture → Stores as blob → Try-on works
- [ ] Clothing type selector works (top/bottom/shoes)
- [ ] Modal closes properly
- [ ] Error messages display clearly
- [ ] Result image displays correctly

### Automated Tests (if implementing)
```python
# pytest tests/test_tryon.py
def test_tryon_upload_with_valid_product():
    # Create test image with person
    # POST to /tryon/upload
    # Assert success=true and image is not empty

def test_tryon_no_pose_detected():
    # Create blank test image
    # POST to /tryon/upload
    # Assert success=false and appropriate message

def test_tryon_invalid_product_id():
    # POST with non-existent product_id
    # Assert 404 status

def test_tryon_requires_auth():
    # POST without auth cookie
    # Assert 401 or redirect status
```

---

## Deployment Checklist

### Before Production
- [ ] Test with real product images
- [ ] Test with various body poses (front, side, different angles)
- [ ] Load test with 10+ concurrent requests
- [ ] Test on mobile devices (iOS/Android)
- [ ] Verify file upload size limits
- [ ] Check CORS configuration for production domain
- [ ] Configure CDN for `/static/images/`
- [ ] Set up database backups
- [ ] Configure error logging
- [ ] Set up monitoring/alerting

### Docker Deployment
```dockerfile
# Dockerfile (if using Docker)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY static/ static/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment-Specific Settings
```python
# For production
import os

MAX_UPLOAD_SIZE = os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)  # 10MB
ENABLE_TRYON_CACHE = os.getenv("ENABLE_TRYON_CACHE", "true")
MEDIAPIPE_BATCH_SIZE = os.getenv("MEDIAPIPE_BATCH_SIZE", 1)
```

---

## Troubleshooting

### Common Issues

**Issue: "Модуль mediapipe не найден"**
```bash
# Solution:
pip install mediapipe==0.10.33 --upgrade
```

**Issue: "Модуль cv2 не найден"**
```bash
# Solution (macOS):
brew install libomp
pip install opencv-python==4.9.0.80 --upgrade

# Solution (Linux):
apt-get install libsm6 libxext6 libxrender-dev
pip install opencv-python==4.9.0.80 --upgrade
```

**Issue: Camera not working in browser**
```javascript
// Check browser permissions:
navigator.mediaDevices.enumerateDevices().then(devices => {
  console.log(devices);
  // Should show video input devices
});

// Ensure HTTPS (or localhost) for camera access
```

**Issue: "Человек не обнаружен" for valid photos**
- Ensure full body is visible (head to feet)
- Try different lighting (good natural light works best)
- Ensure face is visible (improves pose detection)
- Try portrait orientation photos

**Issue: Slow try-on processing**
- Check image resolution (resize if >2MB)
- Monitor backend memory usage
- Consider GPU acceleration (CUDA)
- Check network latency

---

## Next Features to Add

1. **Result History**
   - Store try-ons in database
   - Show user's past try-ons
   - Compare different products

2. **Sharing**
   - Download result as image
   - Share to social media
   - Generate shareable link

3. **AR Preview**
   - WebAR using Three.js
   - Real-time camera feed
   - 3D clothing model overlay

4. **Advanced Filtering**
   - Filter by fit quality
   - Color adjustment tools
   - Size recommendation

5. **Analytics**
   - Track try-on popular products
   - Conversion from try-on to purchase
   - User engagement metrics

---

## Support & Contact

**For Development Help:**
- See [VIRTUAL_TRYON_GUIDE.md](../VIRTUAL_TRYON_GUIDE.md) for technical details
- Check [TRYON_IMPLEMENTATION_SUMMARY.md](../TRYON_IMPLEMENTATION_SUMMARY.md) for feature list

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Code Files:**
- Backend service: `backend/app/services/tryon_service.py`
- Backend router: `backend/app/routers/tryon.py`
- Frontend modal: `frontend/src/components/TryOnModal.jsx`
- Frontend styles: `frontend/src/styles/TryOnModal.css`

---

**Ready to Try-On! 🎨✨**
