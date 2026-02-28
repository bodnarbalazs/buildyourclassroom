import { useEffect, useRef, useState } from "react";
import type { CameraStatus } from "../lib/livefeed-types";
import { useLiveFeedHub } from "../hooks/useLiveFeedHub";
import { useWebRTCSender } from "../hooks/useWebRTC";

export default function LiveFeedCamera() {
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [cameraStatus, setCameraStatus] = useState<CameraStatus>("connecting");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const hub = useLiveFeedHub();
  const { connectionState } = useWebRTCSender(hub, localStream);

  // Acquire camera
  useEffect(() => {
    let cancelled = false;

    async function acquireCamera() {
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: "environment",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      };

      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        setLocalStream(stream);
      } catch {
        // Fallback to front camera
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false,
          });
          if (cancelled) {
            stream.getTracks().forEach((t) => t.stop());
            return;
          }
          setLocalStream(stream);
        } catch (err) {
          if (!cancelled) {
            setCameraStatus("error");
            const name = err instanceof DOMException ? err.name : "";
            setErrorMsg(
              name === "NotAllowedError"
                ? "Camera permission denied"
                : name === "NotFoundError"
                  ? "No camera found"
                  : name === "NotReadableError"
                    ? "Camera in use"
                    : "Camera error",
            );
          }
        }
      }
    }

    acquireCamera();

    return () => {
      cancelled = true;
    };
  }, []);

  // Stop tracks on unmount
  useEffect(() => {
    return () => {
      localStream?.getTracks().forEach((t) => t.stop());
    };
  }, [localStream]);

  // Attach stream to video element
  useEffect(() => {
    if (videoRef.current && localStream) {
      videoRef.current.srcObject = localStream;
    }
  }, [localStream]);

  // Listen for hub events
  useEffect(() => {
    if (hub.state !== "connected") return;

    const handleRejected = (reason: string) => {
      setCameraStatus(
        reason === "No active session" ? "no_session" : "rejected",
      );
      setErrorMsg(reason);
    };

    const handleSessionEnded = () => {
      setCameraStatus("session_ended");
      localStream?.getTracks().forEach((t) => t.stop());
    };

    hub.on("CameraRejected", handleRejected);
    hub.on("SessionEnded", handleSessionEnded);

    return () => {
      hub.off("CameraRejected", handleRejected);
      hub.off("SessionEnded", handleSessionEnded);
    };
  }, [hub, localStream]);

  // Derive status from hub + WebRTC states
  useEffect(() => {
    if (hub.state === "error" || hub.state === "disconnected") {
      setCameraStatus("error");
      setErrorMsg("Connection failed");
      return;
    }
    if (hub.state === "connecting") {
      setCameraStatus("connecting");
      return;
    }
    if (connectionState === "failed") {
      setCameraStatus("error");
      setErrorMsg("Video connection failed");
      return;
    }
    if (connectionState === "disconnected") {
      setCameraStatus("error");
      setErrorMsg("Video connection lost");
      return;
    }
    if (hub.state === "connected" && connectionState === "new") {
      setCameraStatus("waiting_for_session");
      return;
    }
    if (connectionState === "connected") {
      setCameraStatus("streaming");
    }
  }, [hub.state, connectionState]);

  const statusDisplay: Record<CameraStatus, { label: string; color: string }> =
    {
      connecting: { label: "Connecting...", color: "bg-yellow-500" },
      waiting_for_session: {
        label: "Waiting for display...",
        color: "bg-yellow-500",
      },
      streaming: { label: "Streaming", color: "bg-green-500" },
      rejected: { label: errorMsg ?? "Rejected", color: "bg-red-500" },
      no_session: {
        label: "No active session",
        color: "bg-red-500",
      },
      session_ended: { label: "Session ended", color: "bg-gray-500" },
      error: { label: errorMsg ?? "Error", color: "bg-red-500" },
    };

  const { label, color } = statusDisplay[cameraStatus];

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center">
      {/* Viewfinder */}
      {localStream && (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="absolute bottom-4 right-4 w-32 h-24 rounded-lg border border-white/30 object-cover z-10"
        />
      )}

      {/* Status */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
        <span className={`w-3 h-3 rounded-full ${color}`} />
        <span className="text-white text-sm font-medium">{label}</span>
      </div>

      {/* Center message for non-streaming states */}
      {cameraStatus !== "streaming" &&
        cameraStatus !== "connecting" &&
        cameraStatus !== "waiting_for_session" && (
          <p className="text-white text-lg text-center px-8">{label}</p>
        )}
    </div>
  );
}
