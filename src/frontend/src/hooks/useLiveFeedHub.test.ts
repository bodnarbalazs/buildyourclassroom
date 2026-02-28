import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useLiveFeedHub } from "./useLiveFeedHub";

const mockStart = vi.fn();
const mockStop = vi.fn();
const mockInvoke = vi.fn();
const mockOn = vi.fn();
const mockOff = vi.fn();
const mockOnReconnecting = vi.fn();
const mockOnReconnected = vi.fn();
const mockOnClose = vi.fn();

vi.mock("@microsoft/signalr", () => {
  return {
    HubConnectionBuilder: vi.fn().mockImplementation(() => ({
      withUrl: vi.fn().mockReturnThis(),
      withAutomaticReconnect: vi.fn().mockReturnThis(),
      configureLogging: vi.fn().mockReturnThis(),
      build: vi.fn(() => ({
        start: mockStart,
        stop: mockStop,
        invoke: mockInvoke,
        on: mockOn,
        off: mockOff,
        onreconnecting: mockOnReconnecting,
        onreconnected: mockOnReconnected,
        onclose: mockOnClose,
        state: "Connected",
      })),
    })),
    HubConnectionState: { Connected: "Connected" },
    LogLevel: { Warning: 3 },
  };
});

beforeEach(() => {
  vi.clearAllMocks();
  mockStart.mockResolvedValue(undefined);
  mockInvoke.mockResolvedValue(undefined);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("useLiveFeedHub", () => {
  it("connects on mount and calls JoinAsDisplay for display role", async () => {
    renderHook(() => useLiveFeedHub("display"));

    await waitFor(() => {
      expect(mockStart).toHaveBeenCalledOnce();
    });
    expect(mockInvoke).toHaveBeenCalledWith("JoinAsDisplay");
  });

  it("calls JoinAsCamera for camera role", async () => {
    renderHook(() => useLiveFeedHub("camera"));

    await waitFor(() => {
      expect(mockInvoke).toHaveBeenCalledWith("JoinAsCamera");
    });
  });

  it("disconnects on unmount", async () => {
    const { unmount } = renderHook(() => useLiveFeedHub("display"));

    await waitFor(() => expect(mockStart).toHaveBeenCalled());

    unmount();

    expect(mockStop).toHaveBeenCalledOnce();
  });

  it("reports error state on connection failure", async () => {
    mockStart.mockRejectedValueOnce(new Error("fail"));

    const { result } = renderHook(() => useLiveFeedHub("display"));

    await waitFor(() => {
      expect(result.current.state).toBe("error");
    });
  });

  it("transitions to connected state on success", async () => {
    const { result } = renderHook(() => useLiveFeedHub("display"));

    await waitFor(() => {
      expect(result.current.state).toBe("connected");
    });
  });
});
