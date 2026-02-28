import { useEffect, useState, useCallback, useRef } from "react";
import type { CameraId } from "../lib/livefeed-types";
import { useLiveFeedHub } from "../hooks/useLiveFeedHub";
import { useWebRTCReceivers } from "../hooks/useWebRTC";
import { useSnapshotAnalysis } from "../hooks/useSnapshotAnalysis";
import VideoGrid from "../components/livefeed/VideoGrid";
import AttentionBar from "../components/livefeed/AttentionBar";

export default function LiveFeedDisplay() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const videoRefs = useRef<Map<CameraId, HTMLVideoElement>>(new Map());
  const [videoRefsMap, setVideoRefsMap] = useState<
    Map<CameraId, HTMLVideoElement>
  >(new Map());

  const hub = useLiveFeedHub("display");
  const { cameras } = useWebRTCReceivers(hub);
  const { results, collectiveAttention } = useSnapshotAnalysis(
    sessionId,
    videoRefsMap,
  );

  // Create emotion session on mount
  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/emotion/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Live Feed Session" }),
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => setSessionId(data.session_id ?? data.id))
      .catch(() => {});

    return () => controller.abort();
  }, []);

  // End session on unmount
  useEffect(() => {
    return () => {
      if (sessionId) {
        fetch(`/api/emotion/sessions/${sessionId}/end`, { method: "PATCH" });
      }
    };
  }, [sessionId]);

  const handleVideoRef = useCallback(
    (cameraId: CameraId, el: HTMLVideoElement | null) => {
      if (el) {
        videoRefs.current.set(cameraId, el);
      } else {
        videoRefs.current.delete(cameraId);
      }
      setVideoRefsMap(new Map(videoRefs.current));
    },
    [],
  );

  // Build camera entries for the grid
  const gridCameras = new Map(
    Array.from(cameras.entries()).map(([id, cam]) => [
      id,
      {
        stream: cam.stream,
        analysisResult: results.get(id),
      },
    ]),
  );

  return (
    <div className="fixed inset-0 bg-gray-950 flex flex-col">
      {/* Connection status */}
      {hub.state !== "connected" && (
        <div className="absolute top-4 left-4 z-30 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="text-white text-sm">Connecting...</span>
        </div>
      )}

      <VideoGrid cameras={gridCameras} onVideoRef={handleVideoRef} />

      <AttentionBar attention={collectiveAttention} />
    </div>
  );
}
