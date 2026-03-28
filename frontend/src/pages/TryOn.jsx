import React, { useEffect, useRef, useState } from 'react';
import { productsAPI, tryonAPI } from '../services/api';

export function TryOnPage() {
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [resultImage, setResultImage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cameraOpen, setCameraOpen] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    productsAPI
      .list()
      .then((res) => setProducts(res.data || []))
      .catch(() => setProducts([]));

    return () => {
      stopCamera();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, []);

  const onFilePicked = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setError('');
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleDropPhoto = (e) => {
    e.preventDefault();
    onFilePicked(e.dataTransfer.files?.[0]);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      setCameraOpen(true);
      setTimeout(() => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      }, 0);
      setError('');
    } catch {
      setError('Could not access camera');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCameraOpen(false);
  };

  const captureFromCamera = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' });
      onFilePicked(file);
      stopCamera();
    }, 'image/jpeg', 0.95);
  };

  const runTryOn = async () => {
    if (!selectedFile || !selectedProductId) {
      setError('Upload your photo and select item');
      return;
    }

    try {
      setLoading(true);
      setError('');
      const response = await tryonAPI.upload(selectedFile, Number(selectedProductId), 'top');
      if (response.data?.image) {
        setResultImage(`data:image/jpeg;base64,${response.data.image}`);
      } else {
        setError(response.data?.message || 'Try-on failed');
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.message || 'Try-on failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tryon-page">
      <h1>Virtual Try-On</h1>

      <div className="tryon-grid">
        <div
          className="tryon-zone lux-card"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDropPhoto}
        >
          <h3>Upload Your Photo</h3>
          <input type="file" accept="image/*" onChange={(e) => onFilePicked(e.target.files?.[0])} />
          <button className="btn btn-outline tryon-camera-btn" onClick={cameraOpen ? stopCamera : startCamera}>
            ⌾ Use Camera
          </button>

          {cameraOpen && (
            <div className="camera-wrap">
              <video ref={videoRef} autoPlay playsInline muted className="camera-preview" />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
              <button className="btn btn-primary" onClick={captureFromCamera}>Capture</button>
            </div>
          )}

          {previewUrl && <img src={previewUrl} alt="Your upload" className="tryon-preview" />}
        </div>

        <div className="tryon-zone lux-card">
          <h3>Select Item</h3>
          <select value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
            <option value="">Select product</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>{product.name}</option>
            ))}
          </select>
          <p className="subheading">Choose from available catalog products.</p>
        </div>
      </div>

      <div className="tryon-actions">
        <button className="btn btn-primary btn-lg" onClick={runTryOn} disabled={loading}>
          {loading ? 'Trying On...' : 'Try On'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {resultImage && (
        <div className="lux-card result-block">
          <h3>Result</h3>
          <img src={resultImage} alt="Try-on result" className="result-image" />
          <a href={resultImage} download="look.jpg" className="btn btn-outline">Save Look</a>
        </div>
      )}
    </div>
  );
}

const tryOnStyles = `
.tryon-page h1 {
  margin-bottom: 1rem;
}

.tryon-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.tryon-zone {
  min-height: 260px;
  padding: 1rem;
}

.tryon-zone h3 {
  margin-bottom: 0.75rem;
}

.tryon-camera-btn {
  margin-top: 0.7rem;
}

.camera-wrap {
  margin-top: 0.9rem;
}

.camera-preview,
.tryon-preview {
  width: 100%;
  max-height: 340px;
  object-fit: cover;
  border: 1px solid var(--border);
  margin: 0.7rem 0;
}

.tryon-actions {
  display: grid;
  place-items: center;
  margin: 1.1rem 0;
}

.result-block {
  margin-top: 0.8rem;
  display: grid;
  gap: 0.8rem;
}

.result-image {
  width: 100%;
  max-width: 700px;
  margin: 0 auto;
}

@media (max-width: 900px) {
  .tryon-grid {
    grid-template-columns: 1fr;
  }
}
`;

export const TryOnStyles = () => <style>{tryOnStyles}</style>;
