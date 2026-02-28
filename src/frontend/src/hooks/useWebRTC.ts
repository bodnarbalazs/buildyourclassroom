import { useEffect, useRef, useState, useCallback } from "react";
import type { CameraId } from "../lib/livefeed-types";
import { STUN_CONFIG } from "../lib/livefeed-types";
import type { useLiveFeedHub } from "./useLiveFeedHub";

type Hub = ReturnType<typeof useLiveFeedHub>;

// --- Sender (camera page) ---

export function useWebRTCSender(hub: Hub, localStream: MediaStream | null) {
  const [connectionState, setConnectionState] =
    useState<RTCPeerConnectionState>("new");
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const cameraIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (hub.state !== "connected" || !localStream) return;

    const handleOffer = async (cameraId: string, sdp: string) => {
      cameraIdRef.current = cameraId;
      const pc = new RTCPeerConnection(STUN_CONFIG);
      pcRef.current = pc;

      pc.onconnectionstatechange = () => setConnectionState(pc.connectionState);
      pc.onicecandidate = (e) => {
        if (e.candidate) {
          hub.invoke(
            "SendIceCandidate",
            cameraId,
            JSON.stringify(e.candidate),
            false,
          );
        }
      };

      localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

      await pc.setRemoteDescription({ type: "offer", sdp });
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      await hub.invoke("SendAnswer", cameraId, answer.sdp);
    };

    const handleIce = async (_cameraId: string, candidate: string) => {
      if (pcRef.current) {
        await pcRef.current.addIceCandidate(JSON.parse(candidate));
      }
    };

    hub.on("ReceiveOffer", handleOffer);
    hub.on("ReceiveIceCandidate", handleIce);

    return () => {
      hub.off("ReceiveOffer", handleOffer);
      hub.off("ReceiveIceCandidate", handleIce);
      pcRef.current?.close();
      pcRef.current = null;
    };
  }, [hub, localStream]);

  return { connectionState };
}

// --- Receiver (display page) ---

export type CameraStream = {
  stream: MediaStream | null;
  connectionState: RTCPeerConnectionState;
};

export function useWebRTCReceivers(hub: Hub) {
  const [cameras, setCameras] = useState<Map<CameraId, CameraStream>>(
    new Map(),
  );
  const pcsRef = useRef<Map<CameraId, RTCPeerConnection>>(new Map());

  const cleanupCamera = useCallback((cameraId: CameraId) => {
    const pc = pcsRef.current.get(cameraId);
    if (pc) {
      pc.close();
      pcsRef.current.delete(cameraId);
    }
    setCameras((prev) => {
      const next = new Map(prev);
      next.delete(cameraId);
      return next;
    });
  }, []);

  useEffect(() => {
    if (hub.state !== "connected") return;

    const handleCameraJoined = async (cameraId: CameraId) => {
      const pc = new RTCPeerConnection(STUN_CONFIG);
      pcsRef.current.set(cameraId, pc);

      setCameras((prev) =>
        new Map(prev).set(cameraId, { stream: null, connectionState: "new" }),
      );

      pc.onconnectionstatechange = () => {
        setCameras((prev) => {
          const existing = prev.get(cameraId);
          if (!existing) return prev;
          return new Map(prev).set(cameraId, {
            ...existing,
            connectionState: pc.connectionState,
          });
        });
      };

      pc.ontrack = (e) => {
        setCameras((prev) =>
          new Map(prev).set(cameraId, {
            stream: e.streams[0] ?? null,
            connectionState: pc.connectionState,
          }),
        );
      };

      pc.onicecandidate = (e) => {
        if (e.candidate) {
          hub.invoke(
            "SendIceCandidate",
            cameraId,
            JSON.stringify(e.candidate),
            true,
          );
        }
      };

      // Create offer with receive-only video transceiver
      pc.addTransceiver("video", { direction: "recvonly" });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await hub.invoke("SendOffer", cameraId, offer.sdp);
    };

    const handleAnswer = async (cameraId: CameraId, sdp: string) => {
      const pc = pcsRef.current.get(cameraId);
      if (pc) {
        await pc.setRemoteDescription({ type: "answer", sdp });
      }
    };

    const handleIce = async (cameraId: CameraId, candidate: string) => {
      const pc = pcsRef.current.get(cameraId);
      if (pc) {
        await pc.addIceCandidate(JSON.parse(candidate));
      }
    };

    const handleCameraLeft = (cameraId: CameraId) => {
      cleanupCamera(cameraId);
    };

    hub.on("CameraJoined", handleCameraJoined);
    hub.on("ReceiveAnswer", handleAnswer);
    hub.on("ReceiveIceCandidate", handleIce);
    hub.on("CameraLeft", handleCameraLeft);

    return () => {
      hub.off("CameraJoined", handleCameraJoined);
      hub.off("ReceiveAnswer", handleAnswer);
      hub.off("ReceiveIceCandidate", handleIce);
      hub.off("CameraLeft", handleCameraLeft);
      pcsRef.current.forEach((pc) => pc.close());
      pcsRef.current.clear();
    };
  }, [hub, cleanupCamera]);

  return { cameras };
}
