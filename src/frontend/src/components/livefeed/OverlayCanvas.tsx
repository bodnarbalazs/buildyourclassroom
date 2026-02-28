import { useRef, useEffect } from "react";
import type { FaceOverlay } from "../../lib/livefeed-types";
import { ENGAGEMENT_COLORS } from "../../lib/livefeed-types";

export default function OverlayCanvas({
  faces,
  videoEl,
}: {
  faces: FaceOverlay[];
  videoEl: HTMLVideoElement | null;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !videoEl) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const observer = new ResizeObserver(() => {
      canvas.width = videoEl.clientWidth;
      canvas.height = videoEl.clientHeight;
    });
    observer.observe(videoEl);

    return () => observer.disconnect();
  }, [videoEl]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !videoEl) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = videoEl.clientWidth;
    canvas.height = videoEl.clientHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (videoEl.videoWidth === 0) return;

    const scaleX = canvas.width / videoEl.videoWidth;
    const scaleY = canvas.height / videoEl.videoHeight;

    for (const face of faces) {
      const color = ENGAGEMENT_COLORS[face.engagement_level];
      const x = face.bbox.x * scaleX;
      const y = face.bbox.y * scaleY;
      const w = face.bbox.w * scaleX;
      const h = face.bbox.h * scaleY;

      // Semi-transparent fill
      ctx.fillStyle = color + "1a"; // 10% opacity
      ctx.fillRect(x, y, w, h);

      // Border
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      // Label
      ctx.fillStyle = color;
      ctx.font = "12px sans-serif";
      ctx.fillText(face.engagement_level, x, y - 4);
    }
  }, [faces, videoEl]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
    />
  );
}
