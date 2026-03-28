"""Virtual Try-On service with person-adaptive overlay (pose-aware)."""

import base64
import asyncio
import logging
import os
import tempfile
import urllib.request
from io import BytesIO
from typing import Dict, Optional, Tuple

import cv2
import httpx
import numpy as np
import replicate
from PIL import Image
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class TryOnService:
    """Service for virtual try-on functionality using MediaPipe pose + adaptive blending."""

    def __init__(self):
        """Initialize detectors used for body-adaptive placement."""
        self.tryon_provider = (os.getenv("TRYON_PROVIDER", "auto") or "auto").strip().lower()
        self.replicate_api_token = os.getenv("REPLICATE_API_TOKEN", "").strip()
        self.replicate_model = (
            os.getenv("REPLICATE_TRYON_MODEL", "cuuupid/idm-vton") or "cuuupid/idm-vton"
        ).strip()
        self.mp_pose = None

        # Optional MediaPipe Pose for much better anchor quality
        try:
            import importlib

            mp = importlib.import_module("mediapipe")
            self.mp_pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.55,
            )
            logger.info("MediaPipe pose initialized")
        except Exception as e:
            logger.warning(f"MediaPipe pose unavailable, using face/fallback anchors only: {e}")

        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                raise RuntimeError("Failed to load Haar face cascade")
            logger.info("Face detector initialized successfully")
            logger.info(f"Try-on provider mode: {self.tryon_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {e}")
            raise

    def overlay_clothing(
        self,
        user_image_bytes: bytes,
        clothing_image_bytes: bytes,
        clothing_type: str = "top",
    ) -> Tuple[str, bool]:
        """Replicate-only try-on keeping existing router contract (base64, success)."""
        try:
            result = self._process_sync(user_image_bytes, clothing_image_bytes, clothing_type)
            return result.get("result_image", ""), bool(result.get("detected", False))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in overlay_clothing: {str(e)}")
            return "", False

    async def process(
        self,
        user_photo: bytes,
        clothing_image: bytes,
        clothing_type: str,
    ) -> dict:
        return await asyncio.to_thread(self._process_sync, user_photo, clothing_image, clothing_type)

    def _process_sync(
        self,
        user_photo: bytes,
        clothing_image: bytes,
        clothing_type: str,
    ) -> Dict[str, object]:
        token = (os.getenv("REPLICATE_API_TOKEN") or "").strip()
        if not token:
            raise HTTPException(status_code=500, detail="REPLICATE_API_TOKEN не задан")

        user_b64 = base64.b64encode(user_photo).decode("utf-8")
        cloth_b64 = base64.b64encode(clothing_image).decode("utf-8")

        user_uri = f"data:image/jpeg;base64,{user_b64}"
        cloth_uri = f"data:image/jpeg;base64,{cloth_b64}"

        try:
            output = replicate.run(
                "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
                input={
                    "human_img": user_uri,
                    "garm_img": cloth_uri,
                    "garment_des": f"A {clothing_type} clothing item",
                    "category": self._map_category(clothing_type),
                    "is_checked": True,
                    "is_checked_crop": False,
                    "denoise_steps": 30,
                    "seed": 42,
                },
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Replicate API ошибка: {str(e)}")

        output_url = self._extract_output_url(output)
        if not output_url:
            raise HTTPException(status_code=500, detail="Replicate вернул пустой результат")

        with httpx.Client(timeout=120.0) as client:
            response = client.get(output_url)
            response.raise_for_status()
            result_bytes = response.content

        result_b64 = base64.b64encode(result_bytes).decode("utf-8")
        return {
            "result_image": result_b64,
            "detected": True,
            "method": "replicate-idm-vton",
        }

    def _run_external_tryon(
        self,
        user_image_bytes: bytes,
        clothing_image_bytes: bytes,
        clothing_type: str,
    ) -> Optional[str]:
        """Run neural try-on provider (Replicate IDM-VTON) when configured."""
        provider = (self.tryon_provider or "auto").lower()
        if provider == "local":
            return None

        if not self.replicate_api_token:
            if provider in ("premium", "replicate"):
                logger.warning("TRYON_PROVIDER requires REPLICATE_API_TOKEN but token is missing")
            return None

        try:
            import importlib

            replicate = importlib.import_module("replicate")
        except Exception as e:
            logger.warning(f"Replicate SDK is not available, using local try-on: {e}")
            return None

        ct = (clothing_type or "top").lower()
        category_map = {
            "top": "upper_body",
            "bottom": "lower_body",
            "shoes": "lower_body",
        }
        garment_desc_map = {
            "top": "fashion top garment",
            "bottom": "fashion bottom garment",
            "shoes": "fashion shoes",
        }

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg") as user_tmp, tempfile.NamedTemporaryFile(
                suffix=".png"
            ) as cloth_tmp:
                user_tmp.write(user_image_bytes)
                user_tmp.flush()
                cloth_tmp.write(clothing_image_bytes)
                cloth_tmp.flush()

                client = replicate.Client(api_token=self.replicate_api_token)
                with open(user_tmp.name, "rb") as human_img, open(cloth_tmp.name, "rb") as garm_img:
                    output = client.run(
                        self.replicate_model,
                        input={
                            "human_img": human_img,
                            "garm_img": garm_img,
                            "category": category_map.get(ct, "upper_body"),
                            "garment_des": garment_desc_map.get(ct, "fashion garment"),
                            "num_inference_steps": 30,
                        },
                    )

            out_bytes = self._extract_external_output_bytes(output)
            if not out_bytes:
                return None

            out_img = self._load_image(out_bytes, keep_alpha=False)
            if out_img is None:
                return None

            return self._image_to_base64(out_img)
        except Exception as e:
            logger.warning(f"External neural try-on failed, fallback to local pipeline: {e}")
            return None

    def _extract_output_url(self, output) -> Optional[str]:
        if output is None:
            return None
        if isinstance(output, str):
            return output
        if isinstance(output, (list, tuple)) and len(output) > 0:
            return self._extract_output_url(output[0])
        if isinstance(output, dict):
            for key in ("image", "output", "url"):
                if key in output:
                    return self._extract_output_url(output[key])
        if hasattr(output, "url"):
            return str(output.url)
        return str(output)

    def _map_category(self, clothing_type: str) -> str:
        mapping = {
            "top": "upper_body",
            "bottom": "lower_body",
            "shoes": "dresses",
            "dress": "dresses",
        }
        return mapping.get((clothing_type or "").lower(), "upper_body")

    def _extract_external_output_bytes(self, output) -> Optional[bytes]:
        """Extract image bytes from different Replicate output formats."""
        try:
            if output is None:
                return None

            if isinstance(output, (list, tuple)) and len(output) > 0:
                return self._extract_external_output_bytes(output[0])

            if isinstance(output, dict):
                for key in ("image", "output", "url"):
                    if key in output:
                        return self._extract_external_output_bytes(output[key])

            if hasattr(output, "read"):
                return output.read()

            if hasattr(output, "url"):
                return self._download_image_bytes(str(output.url))

            if isinstance(output, str):
                if output.startswith("http://") or output.startswith("https://"):
                    return self._download_image_bytes(output)

                if output.startswith("data:image") and "," in output:
                    return base64.b64decode(output.split(",", 1)[1])

            return None
        except Exception:
            return None

    def _download_image_bytes(self, image_url: str) -> Optional[bytes]:
        """Download image bytes by URL."""
        try:
            with urllib.request.urlopen(image_url, timeout=45) as resp:
                return resp.read()
        except Exception:
            return None

    def _load_image(self, image_bytes: bytes, keep_alpha: bool = False) -> Optional[np.ndarray]:
        """Load image bytes into OpenCV format."""
        try:
            image = Image.open(BytesIO(image_bytes))
            if keep_alpha and image.mode in ("RGBA", "LA"):
                image = image.convert("RGBA")
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)

            image = image.convert("RGB")
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return None

    def _detect_body_anchors(self, user_bgr: np.ndarray) -> Optional[Dict[str, Tuple[int, int]]]:
        """Estimate body anchors from detected face (works well for front portraits)."""
        try:
            h, w = user_bgr.shape[:2]

            # 1) Try MediaPipe pose first for better shoulder/hip/knee/ankle localization
            if self.mp_pose is not None:
                mp_result = self.mp_pose.process(cv2.cvtColor(user_bgr, cv2.COLOR_BGR2RGB))
                if mp_result and mp_result.pose_landmarks and mp_result.pose_landmarks.landmark:
                    lms = mp_result.pose_landmarks.landmark

                    def pt(idx: int) -> Tuple[int, int, float]:
                        lm = lms[idx]
                        return (
                            int(np.clip(lm.x * w, 0, w - 1)),
                            int(np.clip(lm.y * h, 0, h - 1)),
                            float(getattr(lm, "visibility", 1.0)),
                        )

                    lsx, lsy, lsv = pt(11)
                    rsx, rsy, rsv = pt(12)
                    lhx, lhy, lhv = pt(23)
                    rhx, rhy, rhv = pt(24)
                    lkx, lky, lkv = pt(25)
                    rkx, rky, rkv = pt(26)
                    lax, lay, lav = pt(27)
                    rax, ray, rav = pt(28)

                    vis_ok = min(lsv, rsv, lhv, rhv) > 0.35
                    shoulder_span = abs(rsx - lsx)
                    if vis_ok and shoulder_span > max(30, int(w * 0.06)):
                        return {
                            "left_shoulder": (lsx, lsy),
                            "right_shoulder": (rsx, rsy),
                            "left_hip": (lhx, lhy),
                            "right_hip": (rhx, rhy),
                            "left_knee": (lkx, lky),
                            "right_knee": (rkx, rky),
                            "left_ankle": (lax, lay),
                            "right_ankle": (rax, ray),
                        }

            # 2) Face-based heuristic fallback
            gray = cv2.cvtColor(user_bgr, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
            )

            if faces is None or len(faces) == 0:
                return None

            fx, fy, fw, fh = max(faces, key=lambda r: r[2] * r[3])

            shoulder_y = int(fy + fh * 1.65)
            hip_y = int(shoulder_y + fh * 1.95)
            knee_y = int(hip_y + fh * 1.7)
            ankle_y = int(knee_y + fh * 1.4)

            left_shoulder = (int(fx - fw * 0.7), shoulder_y)
            right_shoulder = (int(fx + fw * 1.7), shoulder_y)
            left_hip = (int(fx - fw * 0.35), hip_y)
            right_hip = (int(fx + fw * 1.35), hip_y)
            left_knee = (int(fx - fw * 0.30), knee_y)
            right_knee = (int(fx + fw * 1.30), knee_y)
            left_ankle = (int(fx - fw * 0.22), ankle_y)
            right_ankle = (int(fx + fw * 1.22), ankle_y)

            def clamp_pt(pt: Tuple[int, int]) -> Tuple[int, int]:
                return (max(0, min(w - 1, pt[0])), max(0, min(h - 1, pt[1])))

            return {
                "left_shoulder": clamp_pt(left_shoulder),
                "right_shoulder": clamp_pt(right_shoulder),
                "left_hip": clamp_pt(left_hip),
                "right_hip": clamp_pt(right_hip),
                "left_knee": clamp_pt(left_knee),
                "right_knee": clamp_pt(right_knee),
                "left_ankle": clamp_pt(left_ankle),
                "right_ankle": clamp_pt(right_ankle),
            }
        except Exception as e:
            logger.error(f"Body anchor detection failed: {e}")
            return None

    def _blend_with_seamless_clone(
        self,
        base: np.ndarray,
        overlay_bgr: np.ndarray,
        overlay_alpha: np.ndarray,
        x: int,
        y: int,
    ) -> bool:
        """Use Poisson blending for tops to reduce pasted look. Returns True when applied."""
        try:
            h, w = base.shape[:2]
            oh, ow = overlay_bgr.shape[:2]

            # Seamless clone is stable only when source is fully inside destination.
            if x < 0 or y < 0 or x + ow > w or y + oh > h:
                return False

            a = overlay_alpha[:, :, 0] if overlay_alpha.ndim == 3 else overlay_alpha
            mask = np.clip(a * 255.0, 0, 255).astype(np.uint8)
            _, mask = cv2.threshold(mask, 36, 255, cv2.THRESH_BINARY)

            if int(np.count_nonzero(mask)) < 250:
                return False

            src = overlay_bgr.copy()
            center = (int(x + ow / 2), int(y + oh / 2))

            cloned = cv2.seamlessClone(src, base, mask, center, cv2.NORMAL_CLONE)

            # Mix with mild alpha blend to keep product texture/details.
            alpha_base = base.copy()
            self._blend_with_alpha(alpha_base, overlay_bgr, overlay_alpha, x, y)
            mixed = cv2.addWeighted(cloned, 0.62, alpha_base, 0.38, 0.0)
            base[:, :] = mixed
            return True
        except Exception:
            return False

    def _extract_clothing_foreground(self, clothing_img: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Extract clothing foreground and alpha mask from product image."""
        try:
            if clothing_img.ndim == 3 and clothing_img.shape[2] == 4:
                bgr = clothing_img[:, :, :3]
                alpha = clothing_img[:, :, 3].astype(np.float32) / 255.0
                alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
                return bgr, np.expand_dims(alpha, axis=-1)

            bgr = clothing_img[:, :, :3].copy()
            h, w = bgr.shape[:2]

            mask = np.full((h, w), cv2.GC_PR_FGD, np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)

            # Mark borders as probable background
            border = max(2, int(min(h, w) * 0.03))
            mask[:border, :] = cv2.GC_BGD
            mask[-border:, :] = cv2.GC_BGD
            mask[:, :border] = cv2.GC_BGD
            mask[:, -border:] = cv2.GC_BGD

            # Estimate background color from corners and suppress similar pixels
            patch = max(4, int(min(h, w) * 0.06))
            corners = np.concatenate(
                [
                    bgr[:patch, :patch].reshape(-1, 3),
                    bgr[:patch, -patch:].reshape(-1, 3),
                    bgr[-patch:, :patch].reshape(-1, 3),
                    bgr[-patch:, -patch:].reshape(-1, 3),
                ],
                axis=0,
            )
            bg_color = np.median(corners, axis=0).astype(np.float32)
            dist = np.linalg.norm(bgr.astype(np.float32) - bg_color, axis=2)
            mask[dist < 30.0] = cv2.GC_PR_BGD

            rect = (max(1, int(w * 0.08)), max(1, int(h * 0.05)), int(w * 0.84), int(h * 0.90))
            cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)

            fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
            fg_mask = cv2.GaussianBlur(fg_mask, (7, 7), 0)

            return bgr, np.expand_dims(fg_mask, axis=-1)
        except Exception as e:
            logger.error(f"Foreground extraction failed: {e}")
            return None, None

    def _crop_to_foreground(self, bgr: np.ndarray, alpha: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Crop clothing image to tight foreground bbox to avoid square paste effect."""
        try:
            a = alpha[:, :, 0] if alpha.ndim == 3 else alpha
            ys, xs = np.where(a > 0.08)
            if len(xs) == 0 or len(ys) == 0:
                return bgr, alpha

            x1, x2 = int(xs.min()), int(xs.max())
            y1, y2 = int(ys.min()), int(ys.max())

            pad_x = max(2, int((x2 - x1 + 1) * 0.04))
            pad_y = max(2, int((y2 - y1 + 1) * 0.04))

            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(bgr.shape[1] - 1, x2 + pad_x)
            y2 = min(bgr.shape[0] - 1, y2 + pad_y)

            return bgr[y1:y2 + 1, x1:x2 + 1], alpha[y1:y2 + 1, x1:x2 + 1]
        except Exception:
            return bgr, alpha

    def _warp_top_garment(
        self,
        cloth_bgr: np.ndarray,
        cloth_alpha: np.ndarray,
        lm: Dict[str, Tuple[int, int]],
        img_w: int,
        img_h: int,
        x: int,
        y: int,
        out_w: int,
        out_h: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Apply mild perspective warp for top garments to follow torso shape."""
        try:
            ls = np.array(lm["left_shoulder"], dtype=np.float32)
            rs = np.array(lm["right_shoulder"], dtype=np.float32)
            lh = np.array(lm["left_hip"], dtype=np.float32)
            rh = np.array(lm["right_hip"], dtype=np.float32)

            shoulder_w = max(60.0, float(np.linalg.norm(ls - rs)))
            hip_w = max(55.0, float(np.linalg.norm(lh - rh)))

            shoulder_scale = np.clip((shoulder_w * 1.25) / max(1.0, out_w), 0.70, 1.18)
            hip_scale = np.clip((hip_w * 1.10) / max(1.0, out_w), 0.62, 1.10)

            src_h, src_w = cloth_bgr.shape[:2]
            src = np.array(
                [[0, 0], [src_w - 1, 0], [src_w - 1, src_h - 1], [0, src_h - 1]],
                dtype=np.float32,
            )

            top_w = out_w * shoulder_scale
            bottom_w = out_w * hip_scale
            top_x = (out_w - top_w) / 2.0
            bottom_x = (out_w - bottom_w) / 2.0

            dst = np.array(
                [
                    [top_x, 0],
                    [top_x + top_w, 0],
                    [bottom_x + bottom_w, out_h - 1],
                    [bottom_x, out_h - 1],
                ],
                dtype=np.float32,
            )

            M = cv2.getPerspectiveTransform(src, dst)
            warped_bgr = cv2.warpPerspective(
                cloth_bgr,
                M,
                (out_w, out_h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0),
            )

            a = cloth_alpha[:, :, 0] if cloth_alpha.ndim == 3 else cloth_alpha
            warped_a = cv2.warpPerspective(
                a,
                M,
                (out_w, out_h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )
            warped_a = cv2.GaussianBlur(warped_a, (5, 5), 0)

            return warped_bgr, np.expand_dims(np.clip(warped_a, 0.0, 1.0), axis=-1)
        except Exception:
            resized_bgr = cv2.resize(cloth_bgr, (out_w, out_h), interpolation=cv2.INTER_AREA)
            resized_a = cv2.resize(cloth_alpha, (out_w, out_h), interpolation=cv2.INTER_AREA)
            return resized_bgr, resized_a

    def _restore_skin_foreground(
        self,
        blended: np.ndarray,
        original: np.ndarray,
        overlay_alpha: np.ndarray,
        x: int,
        y: int,
    ) -> None:
        """Restore probable skin pixels from original to keep face/hands in front of clothes."""
        h, w = blended.shape[:2]
        oh, ow = overlay_alpha.shape[:2]

        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w, x + ow), min(h, y + oh)
        if x1 >= x2 or y1 >= y2:
            return

        ox1, oy1 = x1 - x, y1 - y
        ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

        alpha_roi = overlay_alpha[oy1:oy2, ox1:ox2]
        if alpha_roi.ndim == 3:
            alpha_roi = alpha_roi[:, :, 0]

        if float(np.max(alpha_roi)) < 0.12:
            return

        src_roi = original[y1:y2, x1:x2]
        ycrcb = cv2.cvtColor(src_roi, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127)).astype(np.float32) / 255.0

        skin_mask = cv2.GaussianBlur(skin_mask, (5, 5), 0)
        restore_mask = np.clip(skin_mask * (alpha_roi > 0.20).astype(np.float32), 0.0, 1.0)
        if float(np.max(restore_mask)) < 0.05:
            return

        restore_mask = np.expand_dims(restore_mask, axis=-1)
        dst_roi = blended[y1:y2, x1:x2].astype(np.float32)
        src_roi_f = src_roi.astype(np.float32)
        out = src_roi_f * restore_mask + dst_roi * (1.0 - restore_mask)
        blended[y1:y2, x1:x2] = out.astype(np.uint8)

    def _apply_body_constraint_mask(
        self,
        alpha: np.ndarray,
        lm: Dict[str, Tuple[int, int]],
        clothing_type: str,
        x: int,
        y: int,
        img_w: int,
        img_h: int,
    ) -> np.ndarray:
        """Constrain overlay alpha to plausible body region to avoid floating garment look."""
        try:
            a = alpha[:, :, 0] if alpha.ndim == 3 else alpha
            oh, ow = a.shape[:2]

            ls = np.array(lm["left_shoulder"], dtype=np.float32)
            rs = np.array(lm["right_shoulder"], dtype=np.float32)
            lh = np.array(lm["left_hip"], dtype=np.float32)
            rh = np.array(lm["right_hip"], dtype=np.float32)
            lk = np.array(lm["left_knee"], dtype=np.float32)
            rk = np.array(lm["right_knee"], dtype=np.float32)
            la = np.array(lm["left_ankle"], dtype=np.float32)
            ra = np.array(lm["right_ankle"], dtype=np.float32)

            ct = (clothing_type or "top").lower()
            if ct == "bottom":
                pts_global = np.array(
                    [
                        lh + np.array([-18, -20], dtype=np.float32),
                        rh + np.array([18, -20], dtype=np.float32),
                        rk + np.array([10, 18], dtype=np.float32),
                        lk + np.array([-10, 18], dtype=np.float32),
                    ],
                    dtype=np.float32,
                )
            elif ct == "shoes":
                pts_global = np.array(
                    [
                        la + np.array([-24, -20], dtype=np.float32),
                        ra + np.array([24, -20], dtype=np.float32),
                        ra + np.array([24, 24], dtype=np.float32),
                        la + np.array([-24, 24], dtype=np.float32),
                    ],
                    dtype=np.float32,
                )
            else:
                pts_global = np.array(
                    [
                        ls + np.array([-20, -22], dtype=np.float32),
                        rs + np.array([20, -22], dtype=np.float32),
                        rh + np.array([16, 18], dtype=np.float32),
                        lh + np.array([-16, 18], dtype=np.float32),
                    ],
                    dtype=np.float32,
                )

            pts_local = pts_global - np.array([x, y], dtype=np.float32)
            pts_local[:, 0] = np.clip(pts_local[:, 0], -ow * 0.5, ow * 1.5)
            pts_local[:, 1] = np.clip(pts_local[:, 1], -oh * 0.5, oh * 1.5)

            body_mask = np.zeros((oh, ow), dtype=np.float32)
            cv2.fillConvexPoly(body_mask, pts_local.astype(np.int32), 1.0)
            body_mask = cv2.GaussianBlur(body_mask, (19, 19), 0)
            body_mask = np.clip(body_mask, 0.0, 1.0)

            constrained = np.clip(a * body_mask, 0.0, 1.0)

            # Very light border feather to avoid hard alpha edge
            constrained = cv2.GaussianBlur(constrained, (5, 5), 0)
            return np.expand_dims(constrained, axis=-1)
        except Exception:
            return alpha

    def _fit_garment_tone_to_scene(
        self,
        garment_bgr: np.ndarray,
        garment_alpha: np.ndarray,
        user_bgr: np.ndarray,
        x: int,
        y: int,
    ) -> np.ndarray:
        """Match garment color/brightness to local user ROI for more realistic compositing."""
        try:
            h, w = user_bgr.shape[:2]
            gh, gw = garment_bgr.shape[:2]

            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x + gw), min(h, y + gh)
            if x1 >= x2 or y1 >= y2:
                return garment_bgr

            ox1, oy1 = x1 - x, y1 - y
            ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

            g_roi = garment_bgr[oy1:oy2, ox1:ox2].copy()
            a_roi = garment_alpha[oy1:oy2, ox1:ox2]
            if a_roi.ndim == 3:
                a_roi = a_roi[:, :, 0]
            fg = a_roi > 0.18
            if int(np.count_nonzero(fg)) < 40:
                return garment_bgr

            u_roi = user_bgr[y1:y2, x1:x2]

            g_lab = cv2.cvtColor(g_roi, cv2.COLOR_BGR2LAB).astype(np.float32)
            u_lab = cv2.cvtColor(u_roi, cv2.COLOR_BGR2LAB).astype(np.float32)

            g_pix = g_lab[fg]
            u_pix = u_lab.reshape(-1, 3)

            g_mean = np.mean(g_pix, axis=0)
            g_std = np.std(g_pix, axis=0) + 1e-4
            u_mean = np.mean(u_pix, axis=0)
            u_std = np.std(u_pix, axis=0) + 1e-4

            ratio = np.clip(u_std / g_std, 0.55, 1.45)
            g_adj = (g_lab - g_mean) * ratio + u_mean

            # Keep saturation/chroma stable to avoid unnatural recoloring
            g_adj[:, :, 1] = 0.72 * g_adj[:, :, 1] + 0.28 * g_lab[:, :, 1]
            g_adj[:, :, 2] = 0.72 * g_adj[:, :, 2] + 0.28 * g_lab[:, :, 2]

            # Inject local scene shading from user luminance
            l_user = (u_lab[:, :, 0] / 255.0).astype(np.float32)
            l_user = cv2.GaussianBlur(l_user, (9, 9), 0)
            shade = np.clip(0.80 + 0.35 * l_user, 0.72, 1.10)
            g_adj[:, :, 0] = np.clip(g_adj[:, :, 0] * shade, 0, 255)

            g_adj = np.clip(g_adj, 0, 255).astype(np.uint8)
            bgr_adj = cv2.cvtColor(g_adj, cv2.COLOR_LAB2BGR)

            out = garment_bgr.copy()
            out[oy1:oy2, ox1:ox2] = bgr_adj
            return out
        except Exception:
            return garment_bgr

    def _compute_placement(
        self,
        lm: Dict[str, Tuple[int, int]],
        img_w: int,
        img_h: int,
        clothing_type: str,
    ) -> Tuple[int, int, int, int]:
        """Compute overlay box based on body landmarks."""
        ls = np.array(lm["left_shoulder"], dtype=np.float32)
        rs = np.array(lm["right_shoulder"], dtype=np.float32)
        lh = np.array(lm["left_hip"], dtype=np.float32)
        rh = np.array(lm["right_hip"], dtype=np.float32)
        lk = np.array(lm["left_knee"], dtype=np.float32)
        rk = np.array(lm["right_knee"], dtype=np.float32)
        la = np.array(lm["left_ankle"], dtype=np.float32)
        ra = np.array(lm["right_ankle"], dtype=np.float32)

        shoulder_center = (ls + rs) / 2.0
        hip_center = (lh + rh) / 2.0

        shoulder_w = max(60.0, float(np.linalg.norm(ls - rs)))
        hip_w = max(60.0, float(np.linalg.norm(lh - rh)))
        torso_h = max(80.0, float(np.linalg.norm(hip_center - shoulder_center)))
        leg_h = max(100.0, float(np.linalg.norm(((lk + rk) / 2.0) - hip_center)))
        shin_h = max(70.0, float(np.linalg.norm(((la + ra) / 2.0) - ((lk + rk) / 2.0))))

        ct = (clothing_type or "top").lower()

        if ct == "bottom":
            target_w = hip_w * 1.20
            target_h = leg_h * 1.55
            center_x = hip_center[0]
            top_y = hip_center[1] - leg_h * 0.18
        elif ct == "shoes":
            target_w = hip_w * 0.85
            target_h = shin_h * 0.85
            center_x = (la[0] + ra[0]) / 2.0
            top_y = min(la[1], ra[1]) - shin_h * 0.55
        else:  # top/default
            target_w = shoulder_w * 1.30
            target_h = torso_h * 1.55
            center_x = shoulder_center[0]
            top_y = shoulder_center[1] - torso_h * 0.18

        x = int(center_x - target_w / 2)
        y = int(top_y)

        x = max(-img_w // 3, min(x, img_w - 10))
        y = max(-img_h // 3, min(y, img_h - 10))
        target_w = min(target_w, img_w * 1.4)
        target_h = min(target_h, img_h * 1.4)

        return x, y, int(target_w), int(target_h)

    def _fallback_body_anchors(self, img_w: int, img_h: int) -> Dict[str, Tuple[int, int]]:
        """Fallback body anchors when face detection fails."""
        cx = img_w // 2
        shoulder_y = int(img_h * 0.28)
        hip_y = int(img_h * 0.50)
        knee_y = int(img_h * 0.68)
        ankle_y = int(img_h * 0.84)
        shoulder_half = int(img_w * 0.16)
        hip_half = int(img_w * 0.12)

        return {
            "left_shoulder": (cx - shoulder_half, shoulder_y),
            "right_shoulder": (cx + shoulder_half, shoulder_y),
            "left_hip": (cx - hip_half, hip_y),
            "right_hip": (cx + hip_half, hip_y),
            "left_knee": (cx - hip_half, knee_y),
            "right_knee": (cx + hip_half, knee_y),
            "left_ankle": (cx - hip_half, ankle_y),
            "right_ankle": (cx + hip_half, ankle_y),
        }

    def _blend_with_alpha(
        self,
        base: np.ndarray,
        overlay_bgr: np.ndarray,
        overlay_alpha: np.ndarray,
        x: int,
        y: int,
    ) -> None:
        """Blend overlay image into base image in-place with clipping."""
        h, w = base.shape[:2]
        oh, ow = overlay_bgr.shape[:2]

        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w, x + ow), min(h, y + oh)
        if x1 >= x2 or y1 >= y2:
            return

        ox1, oy1 = x1 - x, y1 - y
        ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

        dst = base[y1:y2, x1:x2].astype(np.float32)
        src = overlay_bgr[oy1:oy2, ox1:ox2].astype(np.float32)
        a = overlay_alpha[oy1:oy2, ox1:ox2].astype(np.float32)

        if a.ndim == 2:
            a = np.expand_dims(a, axis=-1)

        a = np.clip(a * 0.88, 0.0, 1.0)
        blended = src * a + dst * (1.0 - a)
        base[y1:y2, x1:x2] = blended.astype(np.uint8)

    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert image to base64 string."""
        try:
            _, buffer = cv2.imencode(".jpg", image)
            return base64.b64encode(buffer.tobytes()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            return ""

