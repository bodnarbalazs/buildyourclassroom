import { useEffect, useRef, useState, useCallback } from "react";
import type {
  CameraId,
  CameraAnalysisResult,
  CollectiveAttention,
  FaceOverlay,
} from "../lib/livefeed-types";
import { SNAPSHOT_INTERVAL_MS } from "../lib/livefeed-types";

function computeAttention(
  results: Map<CameraId, CameraAnalysisResult>,
): CollectiveAttention {
  let totalScore = 0;
  let totalFaces = 0;
  let activeCameras = 0;

  for (const result of results.values()) {
    if (result.faces.length > 0) {
      const camScore =
        result.faces.reduce((sum, f) => sum + f.engagement_score, 0) /
        result.faces.length;
      totalScore += camScore * result.faces.length;
      totalFaces += result.faces.length;
    }
    activeCameras++;
  }

  return {
    score: totalFaces > 0 ? totalScore / totalFaces : 0,
    totalFaces,
    activeCameras,
    maxCameras: 4,
  };
}

export function useSnapshotAnalysis(
  sessionId: string | null,
  cameras: Map<CameraId, HTMLVideoElement>,
) {
  const [results, setResults] = useState<Map<CameraId, CameraAnalysisResult>>(
    new Map(),
  );
  const inFlightRef = useRef<Set<CameraId>>(new Set());
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const captureAndAnalyze = useCallback(
    async (cameraId: CameraId, video: HTMLVideoElement) => {
      if (!sessionId || inFlightRef.current.has(cameraId)) return;
      if (video.videoWidth === 0 || video.videoHeight === 0) return;

      inFlightRef.current.add(cameraId);

      try {
        if (!canvasRef.current) {
          canvasRef.current = document.createElement("canvas");
        }
        const canvas = canvasRef.current;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(video, 0, 0);

        const blob = await new Promise<Blob | null>((resolve) =>
          canvas.toBlob(resolve, "image/jpeg", 0.8),
        );
        if (!blob) return;

        const formData = new FormData();
        formData.append("file", blob, "snapshot.jpg");

        const start = performance.now();
        const res = await fetch(
          `/api/emotion/sessions/${sessionId}/snapshots`,
          { method: "POST", body: formData },
        );

        if (!res.ok) return;

        const data = await res.json();
        const processingMs = performance.now() - start;

        const analysisResult: CameraAnalysisResult = {
          cameraId,
          faces: (data.faces ?? []).map(
            (f: {
              bbox: { x: number; y: number; w: number; h: number };
              dominant_emotion: string;
              engagement_level: string;
              engagement_score: number;
            }): FaceOverlay => ({
              bbox: f.bbox,
              dominant_emotion: f.dominant_emotion,
              engagement_level: f.engagement_level as FaceOverlay["engagement_level"],
              engagement_score: f.engagement_score,
            }),
          ),
          faceCount: data.face_count ?? 0,
          processingMs,
          timestamp: Date.now(),
        };

        setResults((prev) => new Map(prev).set(cameraId, analysisResult));
      } finally {
        inFlightRef.current.delete(cameraId);
      }
    },
    [sessionId],
  );

  useEffect(() => {
    if (!sessionId || cameras.size === 0) return;

    let index = 0;
    let running = true;

    const tick = () => {
      if (!running) return;

      const currentIds = Array.from(cameras.keys());
      if (currentIds.length === 0) {
        setTimeout(tick, SNAPSHOT_INTERVAL_MS);
        return;
      }

      const camId = currentIds[index % currentIds.length];
      const video = cameras.get(camId);
      if (video) {
        captureAndAnalyze(camId, video);
      }

      index++;
      const interval = SNAPSHOT_INTERVAL_MS / currentIds.length;
      setTimeout(tick, interval);
    };

    tick();

    return () => {
      running = false;
    };
  }, [sessionId, cameras, captureAndAnalyze]);

  // Remove results for cameras that no longer exist
  useEffect(() => {
    setResults((prev) => {
      const next = new Map(prev);
      let changed = false;
      for (const key of next.keys()) {
        if (!cameras.has(key)) {
          next.delete(key);
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, [cameras]);

  return {
    results,
    collectiveAttention: computeAttention(results),
  };
}
