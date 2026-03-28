# 🎨 Virtual Try-On Feature - Visual Reference

## Feature Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
└──────────────────────────────────────────────────────────────────────┘

     Products Page
          ↓
    ┌─────────────────────┐
    │  Product Card /     │
    │  Detail Page        │
    │  ┌───────────────┐  │
    │  │ 🎨 Try On Btn│  │ ← User clicks
    │  └───────────────┘  │
    └─────────────────────┘
          ↓
    ┌─────────────────────┐
    │  TryOn Modal Opens   │
    │                     │
    │ ┌─────────────────┐ │
    │ │ 📤 Upload │📷 Cam│ │ ← User chooses mode
    │ └─────────────────┘ │
    └─────────────────────┘
          ↓
    ┌─────────────────────┐       OR        ┌──────────────────────┐
    │ File Upload Mode    │                  │  Camera Mode        │
    │                     │                  │                      │
    │ Click to select or  │                  │ 🎥 Enable camera    │
    │ drag-drop           │                  │ ↓                   │
    │                     │                  │ 📹 Video preview    │
    │ 📸 Photo selected   │                  │ ↓                   │
    │                     │                  │ 📸 Capture photo    │
    └─────────────────────┘                  └──────────────────────┘
          ↓                                          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Select Clothing Type                                   │
    │  ☐ Верх (top)     ☑ Низ (bottom)    ☐ Обувь (shoes)  │
    └─────────────────────────────────────────────────────────┘
          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Click "🎨 Примерить" Button                            │
    │  ⏳ Processing... (2-5 seconds)                         │
    └─────────────────────────────────────────────────────────┘
          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Success: Display Result Image                          │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │ [Result Image]                                  │   │
    │  │ ✨ Ваша примерка готова!                       │   │
    │  └─────────────────────────────────────────────────┘   │
    │                                                         │
    │  [← Назад]  [Готово ✓]                                │
    └─────────────────────────────────────────────────────────┘
          ↓
    User can:
      • Go back and try again
      • Download/share result (future)
      • Close and browse more products
```

---

## Backend Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    INCOMING REQUEST                         │
│  POST /tryon/upload                                         │
│  Content: multipart/form-data                               │
│    ├─ user_photo: Binary JPEG                              │
│    ├─ product_id: 7                                        │
│    └─ clothing_type: "top"                                 │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 1. AUTHENTICATION                                            │
│    ├─ Extract JWT from httpOnly cookie                      │
│    ├─ Verify token signature                                │
│    └─ Get user_id, email, is_admin                         │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. DATABASE LOOKUP                                           │
│    ├─ Query: SELECT * FROM products WHERE id=7             │
│    ├─ Get: Product object with images[], colors[], etc.    │
│    └─ Verify: images[0] exists and is accessible          │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. IMAGE LOADING                                             │
│    ├─ User photo: Load from request bytes                  │
│    │  └─ PIL.Image.open(BytesIO(user_photo_bytes))         │
│    │                                                         │
│    └─ Product photo: Load from file system                 │
│       └─ /backend/static/images/product_7_123456_user.jpg  │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. POSE DETECTION (MediaPipe)                               │
│    ├─ Input: RGB image (user_photo)                        │
│    ├─ Process: MediaPipe Pose (33 landmarks)               │
│    ├─ Output: Landmarks object with coordinates            │
│    │   └─ 11: Left Shoulder, 12: Right Shoulder           │
│    │   └─ 23: Left Hip, 24: Right Hip                      │
│    │   └─ 25: Left Knee, 26: Right Knee                    │
│    │   └─ 27: Left Ankle, 28: Right Ankle                  │
│    │   └─ etc. (33 total)                                  │
│    │                                                         │
│    └─ Check: If NO landmarks → Return 400 "No person"     │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. BODY SEGMENTATION                                        │
│    ├─ Input: RGB image (user_photo)                        │
│    ├─ Process: SelfieSegmentation (MediaPipe)              │
│    └─ Output: Binary mask (0=background, 1=body)           │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. CLOTHING REGION CALCULATION                              │
│                                                               │
│    IF clothing_type == "top":                               │
│    ├─ x_min = min(shoulder_L.x, shoulder_R.x) - padding    │
│    ├─ x_max = max(shoulder_L.x, shoulder_R.x) + padding    │
│    ├─ y_min = min(shoulder_L.y, shoulder_R.y) - padding    │
│    ├─ y_max = max(hip_L.y, hip_R.y) + padding              │
│    └─ region: 200x300px example                            │
│                                                               │
│    IF clothing_type == "bottom":                            │
│    ├─ x_min = min(hip_L.x, hip_R.x) - padding              │
│    ├─ x_max = max(hip_L.x, hip_R.x) + padding              │
│    ├─ y_min = min(hip_L.y, hip_R.y) - padding              │
│    ├─ y_max = max(ankle_L.y, ankle_R.y) + padding          │
│    └─ region: 200x400px example                            │
│                                                               │
│    IF clothing_type == "shoes":                             │
│    ├─ x_min = min(ankle_L.x, ankle_R.x) - padding          │
│    ├─ x_max = max(ankle_L.x, ankle_R.x) + padding          │
│    ├─ y_min = min(ankle_L.y, ankle_R.y) - padding          │
│    ├─ y_max = y_min + (image_height * 0.08)                │
│    └─ region: 200x100px example                            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. CLOTHING IMAGE RESIZE                                    │
│    ├─ Input: Clothing image (arbitrary size)               │
│    ├─ Target: region_width x region_height                 │
│    ├─ Method: cv2.INTER_AREA interpolation                 │
│    └─ Output: Resized clothing image                       │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. ALPHA CHANNEL EXTRACTION                                 │
│    ├─ If clothing is RGBA (PNG with transparency):         │
│    │  └─ alpha = channel[:,:,3] / 255.0                   │
│    │                                                         │
│    └─ If clothing is BGR (JPEG):                            │
│       └─ Auto-generate: alpha = white_pixels * 0.3         │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 9. ALPHA BLENDING (OpenCV)                                  │
│    ├─ For each color channel (R, G, B):                    │
│    │  output[y,x,c] = (clothing[y,x,c] * alpha[y,x]) +    │
│    │                  (background[y,x,c] * (1 - alpha))   │
│    │                                                         │
│    ├─ Result: Realistic clothing overlay                   │
│    └─ Quality: Smooth blending with body contours         │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 10. IMAGE ENCODING                                          │
│    ├─ Input: OpenCV image array (BGR)                      │
│    ├─ Format: JPEG (smaller than PNG for base64)           │
│    ├─ Method: cv2.imencode('.jpg', image)                  │
│    ├─ Encoding: base64.b64encode(jpeg_bytes)               │
│    └─ Output: String "iVBORw0KGgoAAAANS..."               │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│                    RESPONSE (200 OK)                         │
│  {                                                            │
│    "success": true,                                          │
│    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEA...",            │
│    "product_id": 7,                                          │
│    "product_name": "Blue Shirt",                            │
│    "message": "Try-on успешно создана"                     │
│  }                                                            │
└──────────────────────────────────────────────────────────────┘
                   ↓
          Browser receives
          Decodes base64
          Displays result
          User sees ✨
```

---

## MediaPipe Pose Keypoints

```
Position Index Map:

         0 (Nose)
         |
    1 ┌──┴──┐ 2
  Left │ Eye  │ Right
    3 ┌──┴──┐ 4
  Left │ Ear  │ Right
         |
        5
    6   |   7
    ┌───┼───┐
    │       │
    11      12         ← Shoulders (TOP region)
    │       │
    │       │
    │       │
    23      24         ← Hips (BOTTOM region start)
    │       │
    │       │
    25      26         ← Knees
    │       │
    │       │
    27      28         ← Ankles (SHOES region)

Clothing Region Mapping:

TOP:      [shoulder_y ← → hip_y]
         ┌─────────────────┐
         │   CLOTHING      │
         │   ┌─────────┐   │
         │   │ OVERLAY │   │
         │   └─────────┘   │
         └─────────────────┘

BOTTOM:   [hip_y ← → ankle_y]
         ┌─────────────────┐
         │   CLOTHING      │
         │   ┌─────────┐   │
         │   │ OVERLAY │   │
         │   └─────────┘   │
         └─────────────────┘

SHOES:    [ankle_y ← → ankle_y + 8% height]
         ┌─────────────────┐
         │   CLOTHING      │
         │   ┌─────────┐   │
         │   │ OVERLAY │   │
         │   └─────────┘   │
         └─────────────────┘
```

---

## Component State Diagram

### TryOnModal Component

```
Initial State:
  isOpen: false
  loading: false
  error: null
  resultImage: null
  uploadMode: "upload"
  selectedFile: null
  clothingType: "top"
  cameraStream: null

        ↓ User clicks "Try On" button

State: isOpen = true

        ├─ uploadMode = "upload"
        │  ├─ User selects file
        │  └─ selectedFile = File object
        │     └─ Shows file name
        │
        └─ uploadMode = "camera"
           ├─ User enables camera
           ├─ cameraStream = MediaStream
           └─ Shows video feed

        ↓ User clicks "🎨 Примерить"

State: loading = true
       (Shows spinner, disables button)

        ├─ Success path:
        │  ├─ loading = false
        │  ├─ resultImage = "base64..."
        │  └─ Shows result image
        │     ├─ User can click "← Назад"
        │     │  → Reset to upload mode
        │     └─ User can click "Готово ✓"
        │        → Close modal
        │
        └─ Error path:
           ├─ loading = false
           ├─ error = "Error message"
           └─ User can retry with different photo

        ↓ User closes modal

State: isOpen = false
       cameraStream stopped (cleanup)
       All state reset for next use
```

---

## Component File Dependency Tree

```
App.jsx (root)
├── ProductsPage (Products.jsx)
│   ├── ProductCard component
│   │   └── TryOnModal.jsx ⭐ NEW
│   │       └── TryOnModal.css ⭐ NEW
│   │
│   └── ProductDetailPage component
│       └── TryOnModal.jsx ⭐ NEW
│           └── TryOnModal.css ⭐ NEW
│
├── api.js (unchanged, supports multipart)
│   └── fetch POST /tryon/upload
│       └── /tryon/upload endpoint
│           ├── verify_token (auth)
│           ├── TryOnService.overlay_clothing()
│           └── PostgreSQL products table lookup
│
└── Other pages (unaffected)
    ├── HomePage
    ├── AuthPage
    ├── OutfitPage
    └── AdminPage
```

---

## API Endpoint Response Flow

```
Success Response:
{
  "success": true,                              ← Process completed
  "image": "iVBORw0KGgoAAAANSUhEUg...",      ← Base64 JPEG (result)
  "product_id": 7,                             ← Echoed from request
  "product_name": "Blue Shirt",                ← From DB
  "message": "Try-on успешно создана"         ← User message
}

Error Response (No Pose):
{
  "success": false,                            ← Process failed
  "message": "Человек не обнаружен...",       ← User message
  "image": null,                               ← No result
  "product_id": 7,                             ← Context
  "product_name": "Blue Shirt"                 ← Context
}

Error Response (Invalid Input):
{
  "detail": "Invalid clothing_type..."         ← Auto from FastAPI
}  [Status: 400]

Error Response (Not Found):
{
  "detail": "Product with id 999 not found"    ← From router
}  [Status: 404]
```

---

## CSS Styling Structure

```
TryOnModal.css
├── .modal-overlay
│   ├─ position: fixed
│   ├─ backdrop-filter: blur(4px)
│   └─ z-index: 1000
│
├── .modal-content
│   ├─ background: white
│   ├─ border-radius: 16px
│   ├─ animation: slideUp 0.3s
│   └─ display: flex (vertical)
│
├── .modal-header
│   ├─ padding: 20px
│   ├─ border-bottom: 1px solid #e0e0e0
│   └─ .close-btn (absolute positioned)
│
├── .modal-body
│   ├─ flex: 1 (takes available space)
│   ├─ overflow-y: auto
│   └─ Contains:
│       ├─ .mode-selector
│       │  └─ .mode-btn (toggle active state)
│       │
│       ├─ .upload-area
│       │  ├─ .file-input (hidden)
│       │  └─ .upload-label (dashed border)
│       │
│       ├─ .camera-area
│       │  ├─ .camera-video (HTML5 video)
│       │  └─ .camera-controls (buttons)
│       │
│       ├─ .clothing-type-selector
│       │  └─ .clothing-select (dropdown)
│       │
│       └─ .error-message (red box)
│
├── .result-section
│   ├─ .result-image
│   └─ .result-text ("✨ Ваша примерка готова!")
│
├── .modal-footer
│   ├─ display: flex
│   ├─ justify-content: flex-end
│   └─ gap: 12px
│
├── .btn-primary
│   ├─ background: #ff6b6b
│   ├─ color: white
│   └─ hover: #ff5252
│
└── @media (max-width: 768px)
    ├─ .mode-selector → flex-direction: column
    ├─ .camera-controls → flex-direction: column
    ├─ .btn → flex: 1 (full width)
    └─ Modal width reduced to 95%
```

---

## Pose Detection Accuracy

```
Ideal Conditions (High Accuracy ~95%):
├─ Full body visible (head to feet)
├─ Face clearly visible
├─ Good lighting (natural light or bright indoor)
├─ Portrait orientation (vertical)
├─ Minimal occlusion (nothing blocking body parts)
└─ Distance: ~3-10 feet from camera

Challenging Conditions (Medium Accuracy ~60-70%):
├─ Partial body visible
├─ Face not visible
├─ Low lighting
├─ Side/back view
├─ Some occlusion (arms crossed, etc.)
└─ Very close or very far

Failed Conditions (No Detection):
├─ Only face/head visible
├─ Entire body blocked
├─ No person in image
├─ Multiple people (ambiguous)
└─ Extreme angles or distortion
```

---

## Browser Compatibility

```
✅ Chrome/Edge
   ├─ Fetch API: ✅ Full support
   ├─ Canvas API: ✅ Full support
   ├─ MediaDevices.getUserMedia(): ✅ Full support
   ├─ Base64 encoding: ✅ Full support
   └─ HTTPS/localhost: Required for camera

✅ Firefox
   ├─ All features supported
   └─ Same HTTPS/localhost requirement

✅ Safari
   ├─ Fetch API: ✅ Full support
   ├─ Canvas API: ✅ Full support
   ├─ MediaDevices.getUserMedia(): ✅ Supported (iOS 14.5+)
   └─ HTTPS: Required

❌ Internet Explorer
   └─ Not supported (Fetch API, MediaDevices)

📱 Mobile
   ├─ Chrome (Android): ✅ Full support
   ├─ Safari (iOS): ⚠️ Limited (iOS 14.5+)
   └─ Camera access: Requires HTTPS + user permission
```

---

**Visual Reference Complete! 🎨**
