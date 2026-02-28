import type { CameraId, CameraAnalysisResult } from "../../lib/livefeed-types";
import CameraFeed from "./CameraFeed";

type CameraEntry = {
  stream: MediaStream | null;
  analysisResult?: CameraAnalysisResult;
};

const gridClass: Record<number, string> = {
  1: "grid-cols-1",
  2: "grid-cols-2",
  3: "grid-cols-2",
  4: "grid-cols-2",
};

export default function VideoGrid({
  cameras,
  onVideoRef,
}: {
  cameras: Map<CameraId, CameraEntry>;
  onVideoRef?: (cameraId: CameraId, el: HTMLVideoElement | null) => void;
}) {
  const entries = Array.from(cameras.entries());
  const count = entries.length;

  if (count === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-gray-400 text-lg">
          Waiting for cameras... 0/4 connected
        </p>
      </div>
    );
  }

  return (
    <div
      className={`flex-1 grid ${gridClass[count] ?? "grid-cols-2"} gap-2 p-2`}
    >
      {entries.map(([cameraId, { stream, analysisResult }]) => (
        <CameraFeed
          key={cameraId}
          cameraId={cameraId}
          stream={stream}
          faces={analysisResult?.faces ?? []}
          onVideoRef={onVideoRef}
        />
      ))}
    </div>
  );
}
