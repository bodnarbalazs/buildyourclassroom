import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useWebRTCSender, useWebRTCReceivers } from "./useWebRTC";
import type { useLiveFeedHub } from "./useLiveFeedHub";

type Hub = ReturnType<typeof useLiveFeedHub>;

const mockAddTrack = vi.fn();
const mockCreateOffer = vi.fn().mockResolvedValue({ type: "offer", sdp: "offer-sdp" });
const mockCreateAnswer = vi.fn().mockResolvedValue({ type: "answer", sdp: "answer-sdp" });
const mockSetLocalDescription = vi.fn().mockResolvedValue(undefined);
const mockSetRemoteDescription = vi.fn().mockResolvedValue(undefined);
const mockAddIceCandidate = vi.fn().mockResolvedValue(undefined);
const mockClose = vi.fn();
const mockAddTransceiver = vi.fn();

let onConnectionStateChange: (() => void) | null = null;
let onTrack: ((e: { streams: MediaStream[] }) => void) | null = null;
let onIceCandidate: ((e: { candidate: unknown }) => void) | null = null;

function createMockPC() {
  const pc = {
    addTrack: mockAddTrack,
    createOffer: mockCreateOffer,
    createAnswer: mockCreateAnswer,
    setLocalDescription: mockSetLocalDescription,
    setRemoteDescription: mockSetRemoteDescription,
    addIceCandidate: mockAddIceCandidate,
    addTransceiver: mockAddTransceiver,
    close: mockClose,
    connectionState: "new" as RTCPeerConnectionState,
    set onconnectionstatechange(fn: (() => void) | null) {
      onConnectionStateChange = fn;
    },
    set ontrack(fn: ((e: { streams: MediaStream[] }) => void) | null) {
      onTrack = fn;
    },
    set onicecandidate(fn: ((e: { candidate: unknown }) => void) | null) {
      onIceCandidate = fn;
    },
  };
  return pc;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockCreateOffer.mockResolvedValue({ type: "offer", sdp: "offer-sdp" });
  mockCreateAnswer.mockResolvedValue({ type: "answer", sdp: "answer-sdp" });
  mockSetLocalDescription.mockResolvedValue(undefined);
  mockSetRemoteDescription.mockResolvedValue(undefined);
  mockAddIceCandidate.mockResolvedValue(undefined);
  onConnectionStateChange = null;
  onTrack = null;
  onIceCandidate = null;
  vi.stubGlobal("RTCPeerConnection", vi.fn(createMockPC));
});

afterEach(() => {
  vi.restoreAllMocks();
});

function createMockHub(overrides?: Partial<Hub>): Hub {
  const handlers = new Map<string, ((...args: unknown[]) => void)[]>();
  return {
    connection: null,
    state: "connected",
    on: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
      if (!handlers.has(event)) handlers.set(event, []);
      handlers.get(event)!.push(handler);
    }),
    off: vi.fn(),
    invoke: vi.fn().mockResolvedValue(undefined),
    _emit(event: string, ...args: unknown[]) {
      handlers.get(event)?.forEach((h) => h(...args));
    },
    ...overrides,
  } as Hub & { _emit: (event: string, ...args: unknown[]) => void };
}

describe("useWebRTCSender", () => {
  it("creates peer connection on ReceiveOffer", async () => {
    const hub = createMockHub();
    const stream = { getTracks: () => [{ kind: "video" }] } as unknown as MediaStream;

    renderHook(() => useWebRTCSender(hub, stream));

    // Simulate receiving an offer
    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("ReceiveOffer", "cam-1", "offer-sdp");
    });

    expect(RTCPeerConnection).toHaveBeenCalled();
    expect(mockSetRemoteDescription).toHaveBeenCalledWith({
      type: "offer",
      sdp: "offer-sdp",
    });
  });

  it("adds local tracks to peer connection", async () => {
    const hub = createMockHub();
    const track1 = { kind: "video" };
    const track2 = { kind: "audio" };
    const stream = {
      getTracks: () => [track1, track2],
    } as unknown as MediaStream;

    renderHook(() => useWebRTCSender(hub, stream));

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("ReceiveOffer", "cam-1", "offer-sdp");
    });

    expect(mockAddTrack).toHaveBeenCalledTimes(2);
  });

  it("creates and sends answer", async () => {
    const hub = createMockHub();
    const stream = { getTracks: () => [] } as unknown as MediaStream;

    renderHook(() => useWebRTCSender(hub, stream));

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("ReceiveOffer", "cam-1", "offer-sdp");
    });

    expect(mockCreateAnswer).toHaveBeenCalled();
    expect(hub.invoke).toHaveBeenCalledWith("SendAnswer", "cam-1", "answer-sdp");
  });
});

describe("useWebRTCReceivers", () => {
  it("creates offer on CameraJoined", async () => {
    const hub = createMockHub();

    renderHook(() => useWebRTCReceivers(hub));

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("CameraJoined", "cam-1");
    });

    expect(RTCPeerConnection).toHaveBeenCalled();
    expect(mockCreateOffer).toHaveBeenCalled();
    expect(hub.invoke).toHaveBeenCalledWith("SendOffer", "cam-1", "offer-sdp");
  });

  it("sets answer on ReceiveAnswer", async () => {
    const hub = createMockHub();

    renderHook(() => useWebRTCReceivers(hub));

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("CameraJoined", "cam-1");
    });

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("ReceiveAnswer", "cam-1", "answer-sdp");
    });

    expect(mockSetRemoteDescription).toHaveBeenCalledWith({
      type: "answer",
      sdp: "answer-sdp",
    });
  });

  it("cleans up on CameraLeft", async () => {
    const hub = createMockHub();

    const { result } = renderHook(() => useWebRTCReceivers(hub));

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("CameraJoined", "cam-1");
    });

    expect(result.current.cameras.has("cam-1")).toBe(true);

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("CameraLeft", "cam-1");
    });

    expect(result.current.cameras.has("cam-1")).toBe(false);
    expect(mockClose).toHaveBeenCalled();
  });

  it("adds receive-only video transceiver", async () => {
    const hub = createMockHub();

    renderHook(() => useWebRTCReceivers(hub));

    await act(async () => {
      (hub as Hub & { _emit: Function })._emit("CameraJoined", "cam-1");
    });

    expect(mockAddTransceiver).toHaveBeenCalledTimes(1);
    expect(mockAddTransceiver).toHaveBeenCalledWith("video", {
      direction: "recvonly",
    });
  });
});
