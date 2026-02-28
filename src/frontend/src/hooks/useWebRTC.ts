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
  const localStreamRef = useRef<MediaStream | null>(null);
  const pendingOfferRef = useRef<{ cameraId: string; sdp: string } | null>(
    null,
  );
  const remoteDescSetRef = useRef(false);
  const iceCandidateQueueRef = useRef<RTCIceCandidateInit[]>([]);

  localStreamRef.current = localStream;

  const processOffer = useCallback(
    async (cameraId: string, sdp: string, stream: MediaStream) => {
      try {
        cameraIdRef.current = cameraId;
        const pc = new RTCPeerConnection(STUN_CONFIG);
        pcRef.current = pc;

        pc.onconnectionstatechange = () =>
          setConnectionState(pc.connectionState);
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

        stream.getTracks().forEach((track) => pc.addTrack(track, stream));

        await pc.setRemoteDescription({ type: "offer", sdp });
        remoteDescSetRef.current = true;

        // Flush ICE candidates that arrived before remote description was set
        for (const candidate of iceCandidateQueueRef.current) {
          await pc.addIceCandidate(candidate);
        }
        iceCandidateQueueRef.current = [];

        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        await hub.invoke("SendAnswer", cameraId, answer.sdp);
      } catch (err) {
        console.error("[WebRTC Sender] Failed to process offer:", err);
      }
    },
    [hub],
  );

  // Process buffered offer once localStream becomes available
  useEffect(() => {
    if (!localStream || !pendingOfferRef.current) return;
    const { cameraId, sdp } = pendingOfferRef.current;
    pendingOfferRef.current = null;
    processOffer(cameraId, sdp, localStream);
  }, [localStream, processOffer]);

  useEffect(() => {
    if (hub.state !== "connected") return;

    const handleOffer = async (cameraId: string, sdp: string) => {
      const stream = localStreamRef.current;
      if (!stream) {
        // Offer arrived before getUserMedia completed — buffer it
        pendingOfferRef.current = { cameraId, sdp };
        return;
      }
      await processOffer(cameraId, sdp, stream);
    };

    const handleIce = async (_cameraId: string, candidate: string) => {
      try {
        if (!remoteDescSetRef.current) {
          iceCandidateQueueRef.current.push(JSON.parse(candidate));
          return;
        }
        if (pcRef.current) {
          await pcRef.current.addIceCandidate(JSON.parse(candidate));
        }
      } catch (err) {
        console.error("[WebRTC Sender] Failed to add ICE candidate:", err);
      }
    };

    hub.on("ReceiveOffer", handleOffer);
    hub.on("ReceiveIceCandidate", handleIce);

    return () => {
      hub.off("ReceiveOffer", handleOffer);
      hub.off("ReceiveIceCandidate", handleIce);
      pcRef.current?.close();
      pcRef.current = null;
      remoteDescSetRef.current = false;
      iceCandidateQueueRef.current = [];
      pendingOfferRef.current = null;
    };
  }, [hub, processOffer]);

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
  const remoteDescSetRef = useRef<Set<CameraId>>(new Set());
  const iceCandidateQueuesRef = useRef<Map<CameraId, RTCIceCandidateInit[]>>(
    new Map(),
  );

  const cleanupCamera = useCallback((cameraId: CameraId) => {
    const pc = pcsRef.current.get(cameraId);
    if (pc) {
      pc.close();
      pcsRef.current.delete(cameraId);
    }
    remoteDescSetRef.current.delete(cameraId);
    iceCandidateQueuesRef.current.delete(cameraId);
    setCameras((prev) => {
      const next = new Map(prev);
      next.delete(cameraId);
      return next;
    });
  }, []);

  useEffect(() => {
    if (hub.state !== "connected") return;

    const handleCameraJoined = async (cameraId: CameraId) => {
      try {
        const pc = new RTCPeerConnection(STUN_CONFIG);
        pcsRef.current.set(cameraId, pc);

        setCameras((prev) =>
          new Map(prev).set(cameraId, {
            stream: null,
            connectionState: "new",
          }),
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
      } catch (err) {
        console.error("[WebRTC Receiver] Failed to handle camera join:", err);
      }
    };

    const handleAnswer = async (cameraId: CameraId, sdp: string) => {
      try {
        const pc = pcsRef.current.get(cameraId);
        if (!pc) return;

        await pc.setRemoteDescription({ type: "answer", sdp });
        remoteDescSetRef.current.add(cameraId);

        // Flush ICE candidates that arrived before the answer
        const queued = iceCandidateQueuesRef.current.get(cameraId);
        if (queued) {
          for (const candidate of queued) {
            await pc.addIceCandidate(candidate);
          }
          iceCandidateQueuesRef.current.delete(cameraId);
        }
      } catch (err) {
        console.error("[WebRTC Receiver] Failed to handle answer:", err);
      }
    };

    const handleIce = async (cameraId: CameraId, candidate: string) => {
      try {
        const pc = pcsRef.current.get(cameraId);
        if (!pc) return;

        if (!remoteDescSetRef.current.has(cameraId)) {
          const queue =
            iceCandidateQueuesRef.current.get(cameraId) ?? [];
          queue.push(JSON.parse(candidate));
          iceCandidateQueuesRef.current.set(cameraId, queue);
          return;
        }

        await pc.addIceCandidate(JSON.parse(candidate));
      } catch (err) {
        console.error("[WebRTC Receiver] Failed to add ICE candidate:", err);
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
      remoteDescSetRef.current.clear();
      iceCandidateQueuesRef.current.clear();
    };
  }, [hub, cleanupCamera]);

  return { cameras };
}
