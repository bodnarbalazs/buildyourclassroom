import { useEffect, useRef } from "react";
import type { CameraId, FaceOverlay } from "../../lib/livefeed-types";
import OverlayCanvas from "./OverlayCanvas";

export default function CameraFeed({
  cameraId,
  stream,
  faces,
  onVideoRef,
}: {
  cameraId: CameraId;
  stream: MediaStream | null;
  faces: FaceOverlay[];
  onVideoRef?: (cameraId: CameraId, el: HTMLVideoElement | null) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  useEffect(() => {
    onVideoRef?.(cameraId, videoRef.current);
    return () => onVideoRef?.(cameraId, null);
  }, [cameraId, onVideoRef]);

  const label = `Camera ${cameraId.replace("cam-", "")}`;

  return (
    <div className="relative bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
      />
      <OverlayCanvas faces={faces} videoEl={videoRef.current} />
      <span className="absolute top-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
        {label}
      </span>
    </div>
  );
}
