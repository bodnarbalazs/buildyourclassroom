import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useSnapshotAnalysis } from "./useSnapshotAnalysis";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", mockFetch);

  // Mock canvas
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    drawImage: vi.fn(),
  })) as unknown as typeof HTMLCanvasElement.prototype.getContext;

  HTMLCanvasElement.prototype.toBlob = vi.fn(function (
    this: HTMLCanvasElement,
    cb: (blob: Blob | null) => void,
  ) {
    cb(new Blob(["test"], { type: "image/jpeg" }));
  }) as unknown as typeof HTMLCanvasElement.prototype.toBlob;
});

function makeVideoEl(): HTMLVideoElement {
  return {
    videoWidth: 640,
    videoHeight: 480,
  } as unknown as HTMLVideoElement;
}

function makeApiResponse(faceCount = 1) {
  return new Response(
    JSON.stringify({
      face_count: faceCount,
      faces: Array.from({ length: faceCount }, (_, i) => ({
        bbox: { x: 10 * i, y: 10 * i, w: 50, h: 50 },
        dominant_emotion: "happy",
        engagement_level: "engaged",
        engagement_score: 0.8,
      })),
    }),
    { status: 200 },
  );
}

describe("useSnapshotAnalysis", () => {
  it("updates results on successful response", async () => {
    mockFetch.mockResolvedValue(makeApiResponse(2));

    const cameras = new Map([["cam-1", makeVideoEl()]]);
    const { result } = renderHook(() =>
      useSnapshotAnalysis("session-1", cameras),
    );

    await waitFor(
      () => {
        expect(result.current.results.has("cam-1")).toBe(true);
      },
      { timeout: 3000 },
    );

    const camResult = result.current.results.get("cam-1");
    expect(camResult?.faceCount).toBe(2);
    expect(camResult?.faces).toHaveLength(2);
  });

  it("calculates weighted attention score", async () => {
    mockFetch.mockResolvedValue(makeApiResponse(3));

    const cameras = new Map([["cam-1", makeVideoEl()]]);
    const { result } = renderHook(() =>
      useSnapshotAnalysis("session-1", cameras),
    );

    await waitFor(
      () => {
        expect(result.current.collectiveAttention.totalFaces).toBe(3);
      },
      { timeout: 3000 },
    );

    expect(result.current.collectiveAttention.score).toBeCloseTo(0.8);
  });

  it("pauses with zero cameras", async () => {
    const cameras = new Map<string, HTMLVideoElement>();
    renderHook(() => useSnapshotAnalysis("session-1", cameras));

    // Wait long enough to confirm no fetch calls
    await new Promise((r) => setTimeout(r, 100));

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("does nothing without a session ID", async () => {
    const cameras = new Map([["cam-1", makeVideoEl()]]);
    renderHook(() => useSnapshotAnalysis(null, cameras));

    await new Promise((r) => setTimeout(r, 100));

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("keeps previous result on API error", async () => {
    // First call succeeds
    mockFetch.mockResolvedValueOnce(makeApiResponse(1));
    // Second call fails
    mockFetch.mockResolvedValueOnce(new Response("error", { status: 500 }));

    const cameras = new Map([["cam-1", makeVideoEl()]]);
    const { result } = renderHook(() =>
      useSnapshotAnalysis("session-1", cameras),
    );

    await waitFor(
      () => {
        expect(result.current.results.has("cam-1")).toBe(true);
      },
      { timeout: 3000 },
    );

    // Wait for second call to fail
    await waitFor(
      () => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      },
      { timeout: 3000 },
    );

    // Previous result should still be there
    expect(result.current.results.has("cam-1")).toBe(true);
    expect(result.current.results.get("cam-1")?.faceCount).toBe(1);
  });
});
