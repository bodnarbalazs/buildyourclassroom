import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import LiveFeedCamera from "./LiveFeedCamera";

// Mock hooks
const mockHubState = { current: "connecting" as string };
const mockConnectionState = { current: "new" as string };
const hubHandlers = new Map<string, ((...args: unknown[]) => void)[]>();

vi.mock("../hooks/useLiveFeedHub", () => ({
  useLiveFeedHub: () => ({
    connection: null,
    state: mockHubState.current,
    on: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
      if (!hubHandlers.has(event)) hubHandlers.set(event, []);
      hubHandlers.get(event)!.push(handler);
    }),
    off: vi.fn(),
    invoke: vi.fn(),
  }),
}));

vi.mock("../hooks/useWebRTC", () => ({
  useWebRTCSender: () => ({
    connectionState: mockConnectionState.current,
  }),
}));

const mockGetUserMedia = vi.fn();
const mockStopTrack = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  hubHandlers.clear();
  mockHubState.current = "connected";
  mockConnectionState.current = "new";
  mockGetUserMedia.mockResolvedValue({
    getTracks: () => [{ stop: mockStopTrack, kind: "video" }],
  });
  vi.stubGlobal("navigator", {
    mediaDevices: { getUserMedia: mockGetUserMedia },
  });
  // happy-dom validates srcObject type — stub it out
  Object.defineProperty(HTMLVideoElement.prototype, "srcObject", {
    set: vi.fn(),
    get: vi.fn(() => null),
    configurable: true,
  });
});

function findText(text: string) {
  return screen.getAllByText(text).length > 0;
}

describe("LiveFeedCamera", () => {
  it("requests camera on mount", async () => {
    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledWith(
        expect.objectContaining({
          video: expect.objectContaining({
            facingMode: "environment",
          }),
        }),
      );
    });
  });

  it("shows waiting state when connected but no WebRTC", async () => {
    mockHubState.current = "connected";
    mockConnectionState.current = "new";

    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(findText("Waiting for display...")).toBe(true);
    });
  });

  it("shows streaming state when WebRTC connected", async () => {
    mockHubState.current = "connected";
    mockConnectionState.current = "connected";

    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(findText("Streaming")).toBe(true);
    });
  });

  it("shows rejection when room full", async () => {
    mockHubState.current = "connected";
    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(hubHandlers.has("CameraRejected")).toBe(true);
    });

    act(() => {
      hubHandlers
        .get("CameraRejected")!
        .forEach((h) => h("4/4 streams active. Please try again later."));
    });

    await waitFor(() => {
      expect(
        findText("4/4 streams active. Please try again later."),
      ).toBe(true);
    });
  });

  it("shows no-session when no display active", async () => {
    mockHubState.current = "connected";
    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(hubHandlers.has("CameraRejected")).toBe(true);
    });

    act(() => {
      hubHandlers
        .get("CameraRejected")!
        .forEach((h) => h("No active session"));
    });

    await waitFor(() => {
      expect(findText("No active session")).toBe(true);
    });
  });

  it("shows session-ended when display disconnects", async () => {
    mockHubState.current = "connected";
    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(hubHandlers.has("SessionEnded")).toBe(true);
    });

    act(() => {
      hubHandlers.get("SessionEnded")!.forEach((h) => h());
    });

    await waitFor(() => {
      expect(findText("Session ended")).toBe(true);
    });
  });

  it("shows error on camera permission denied", async () => {
    mockGetUserMedia.mockRejectedValue(new Error("NotAllowedError"));

    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(findText("Camera permission denied")).toBe(true);
    });
  });

  it("stops media tracks on unmount", async () => {
    const { unmount } = render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalled();
    });

    unmount();

    expect(mockStopTrack).toHaveBeenCalled();
  });

  it("stops tracks when unmounted during getUserMedia", async () => {
    let resolveGetUserMedia!: (stream: MediaStream) => void;
    mockGetUserMedia.mockReturnValue(
      new Promise((resolve) => {
        resolveGetUserMedia = resolve;
      }),
    );

    const { unmount } = render(<LiveFeedCamera />);
    unmount();

    // Stream resolves after unmount — tracks must still be stopped
    await act(async () => {
      resolveGetUserMedia({
        getTracks: () => [{ stop: mockStopTrack, kind: "video" }],
      } as unknown as MediaStream);
    });

    expect(mockStopTrack).toHaveBeenCalled();
  });

  it("falls back to front camera if rear unavailable", async () => {
    mockGetUserMedia
      .mockRejectedValueOnce(new Error("rear not available"))
      .mockResolvedValueOnce({
        getTracks: () => [{ stop: mockStopTrack, kind: "video" }],
      });

    render(<LiveFeedCamera />);

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledTimes(2);
    });

    // Second call should not have facingMode
    const secondCall = mockGetUserMedia.mock.calls[1][0];
    expect(secondCall.video.facingMode).toBeUndefined();
  });
});
