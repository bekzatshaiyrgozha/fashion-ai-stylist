import { useState, useRef, useEffect } from "react";
import "../styles/TryOnModal.css";

export default function TryOnModal({
  isOpen,
  onClose,
  product,
  onSuccess,
  userId,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [uploadMode, setUploadMode] = useState("upload"); // "upload" or "camera"
  const [selectedFile, setSelectedFile] = useState(null);
  const [clothingType, setClothingType] = useState("auto");
  const [cameraStream, setCameraStream] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const inferClothingType = () => {
    const category = (product?.category || "").toLowerCase();
    const name = (product?.name || "").toLowerCase();

    if (category.includes("shoe") || category.includes("обув") || name.includes("shoe") || name.includes("кроссов") || name.includes("ботин")) {
      return "shoes";
    }

    if (category.includes("bottom") || category.includes("pants") || category.includes("skirt") || category.includes("низ") || name.includes("брюк") || name.includes("джинс") || name.includes("юбк")) {
      return "bottom";
    }

    return "top";
  };

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream]);

  const startCamera = async () => {
    try {
      setError(null);
      
      // Request camera with fallback constraints
      const constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user"
        },
        audio: false
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setCameraStream(stream);
      
      // Set video source with delay to ensure element is ready
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(err => {
            console.error("Error playing video:", err);
            setError("Ошибка при запуске видео");
          });
        }
      }, 100);
    } catch (err) {
      console.error("Camera error:", err);
      let errorMsg = "Не удалось получить доступ к камере";
      
      if (err.name === 'NotAllowedError') {
        errorMsg = "Доступ к камере запрещен. Проверьте разрешения браузера";
      } else if (err.name === 'NotFoundError') {
        errorMsg = "Камера не найдена. Проверьте наличие камеры";
      } else if (err.name === 'NotReadableError') {
        errorMsg = "Камера занята другим приложением";
      }
      
      setError(errorMsg);
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
  };

  const captureFromCamera = async () => {
    if (!videoRef.current || !canvasRef.current) {
      setError("Видео не загружено");
      return;
    }

    try {
      const video = videoRef.current;
      
      // Wait for video to be ready
      if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        setError("Пожалуйста, подождите пока видео загрузится");
        return;
      }

      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw image with proper orientation
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        if (blob) {
          // Convert blob to File for consistency
          const file = new File([blob], "camera-photo.jpg", { type: "image/jpeg" });
          setSelectedFile(file);
          stopCamera();
          setUploadMode("upload");
          setError(null);
        } else {
          setError("Ошибка при создании изображения");
        }
      }, "image/jpeg", 0.95);
    } catch (err) {
      setError("Ошибка при захвате изображения: " + err.message);
      console.error("Capture error:", err);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const processAndUpload = async () => {
    if (!selectedFile) {
      setError("Пожалуйста, выберите или сделайте фото");
      return;
    }

    if (!product || !product.id) {
      setError("Ошибка: товар не загружен");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resolvedClothingType = clothingType === "auto" ? inferClothingType() : clothingType;

      const formData = new FormData();
      formData.append("user_photo", selectedFile);
      formData.append("product_id", product.id);
      formData.append("clothing_type", resolvedClothingType);

      console.log("Sending try-on request with:", {
        product_id: product.id,
        clothing_type: resolvedClothingType,
        file_size: selectedFile.size
      });

      const response = await fetch("/api/tryon/upload", {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      console.log("Response status:", response.status);

      if (!response.ok) {
        let errorMsg = "Ошибка при обработке изображения";
        try {
          const errorData = await response.json();
          errorMsg = errorData.message || errorData.detail || errorMsg;
        } catch (e) {
          errorMsg = `Ошибка ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();
      console.log("Result:", result);

      if (!result.success) {
        setError(result.message || "Try-on не удалась");
        return;
      }

      if (!result.image) {
        setError("Не получено изображение результата");
        return;
      }

      setResultImage(`data:image/jpeg;base64,${result.image}`);
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      setError(err.message || "Ошибка при загрузке");
      console.error("Upload error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Примерка одежды</h2>
          {product && <p className="product-name">{product.name}</p>}
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {!resultImage ? (
            <div className="upload-section">
              <div className="mode-selector">
                <button
                  className={`mode-btn ${uploadMode === "upload" ? "active" : ""}`}
                  onClick={() => {
                    setUploadMode("upload");
                    stopCamera();
                  }}
                >
                  📤 Загрузить фото
                </button>
                <button
                  className={`mode-btn ${uploadMode === "camera" ? "active" : ""}`}
                  onClick={() => {
                    setUploadMode("camera");
                    if (!cameraStream) startCamera();
                  }}
                >
                  📷 Камера
                </button>
              </div>

              {uploadMode === "upload" && (
                <div className="upload-area">
                  <input
                    type="file"
                    id="photo-input"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  <label htmlFor="photo-input" className="upload-label">
                    <div className="upload-icon">📸</div>
                    <p>Нажмите для выбора фото</p>
                    {selectedFile && (
                      <p className="file-name">{selectedFile.name}</p>
                    )}
                  </label>
                </div>
              )}

              {uploadMode === "camera" && (
                <div className="camera-area">
                  {cameraStream ? (
                    <>
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="camera-video"
                        onError={(e) => {
                          console.error("Video error:", e);
                          setError("Ошибка при воспроизведении видео");
                        }}
                        onLoadedMetadata={() => {
                          console.log("Video loaded, dimensions:", videoRef.current?.videoWidth, "x", videoRef.current?.videoHeight);
                        }}
                      />
                      <canvas ref={canvasRef} style={{ display: "none" }} />
                      <div className="camera-controls">
                        <button
                          className="btn btn-primary"
                          onClick={captureFromCamera}
                        >
                          📸 Сделать фото
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={stopCamera}
                        >
                          ✕ Закрыть камеру
                        </button>
                      </div>
                    </>
                  ) : (
                    <button
                      className="btn btn-primary"
                      onClick={startCamera}
                      style={{ width: "100%" }}
                    >
                      🎥 Включить камеру
                    </button>
                  )}
                </div>
              )}

              <div className="clothing-type-selector">
                <label>Тип одежды:</label>
                <select
                  value={clothingType}
                  onChange={(e) => setClothingType(e.target.value)}
                  className="clothing-select"
                >
                  <option value="auto">Авто (рекомендуется)</option>
                  <option value="top">Верх (рубашка, свитер)</option>
                  <option value="bottom">Низ (штаны, юбка)</option>
                  <option value="shoes">Обувь</option>
                </select>
              </div>

              <div className="ai-tryon-hint">
                ✨ Powered by AI — реалистичная примерка занимает 10-20 секунд
                <br />
                📸 Фото в полный рост даёт лучший результат
              </div>

              {error && <div className="error-message">{error}</div>}
            </div>
          ) : (
            <div className="result-section">
              <img src={resultImage} alt="Try-on result" className="result-image" />
              <p className="result-text">✨ Ваша примерка готова!</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {!resultImage ? (
            <>
              <button className="btn btn-secondary" onClick={onClose}>
                Отмена
              </button>
              <button
                className="btn btn-primary"
                onClick={processAndUpload}
                disabled={loading || !selectedFile}
              >
                {loading ? "⏳ Обработка..." : "🎨 Примерить"}
              </button>
            </>
          ) : (
            <>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setResultImage(null);
                  setSelectedFile(null);
                }}
              >
                ← Назад
              </button>
              <button className="btn btn-primary" onClick={onClose}>
                Готово ✓
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
