export type CameraId = string; // "cam-1" through "cam-4"

export type CameraStatus =
  | "connecting"
  | "waiting_for_session"
  | "streaming"
  | "rejected"
  | "no_session"
  | "session_ended"
  | "error";

export type DisplayCameraState = {
  cameraId: CameraId;
  stream: MediaStream | null;
  connectionState: RTCPeerConnectionState;
};

export type FaceOverlay = {
  bbox: { x: number; y: number; w: number; h: number };
  dominant_emotion: string;
  engagement_level: "engaged" | "passive" | "confused" | "anxious" | "disruptive";
  engagement_score: number;
};

export type CameraAnalysisResult = {
  cameraId: CameraId;
  faces: FaceOverlay[];
  faceCount: number;
  processingMs: number;
  timestamp: number;
};

export type CollectiveAttention = {
  score: number; // 0-1, weighted average
  totalFaces: number;
  activeCameras: number;
  maxCameras: 4;
};

export const STUN_CONFIG: RTCConfiguration = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" },
    {
      urls: "turn:staticauth.openrelay.metered.ca:443",
      username: "openrelayproject",
      credential: "openrelayprojectsecret",
    },
    {
      urls: "turn:staticauth.openrelay.metered.ca:443?transport=tcp",
      username: "openrelayproject",
      credential: "openrelayprojectsecret",
    },
  ],
};

export const MAX_CAMERAS = 4;
export const SNAPSHOT_INTERVAL_MS = 1000;

export const ENGAGEMENT_COLORS: Record<FaceOverlay["engagement_level"], string> = {
  engaged: "#22c55e",
  passive: "#eab308",
  confused: "#f97316",
  anxious: "#f97316",
  disruptive: "#ef4444",
};
