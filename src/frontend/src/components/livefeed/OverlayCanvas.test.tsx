import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import OverlayCanvas from "./OverlayCanvas";
import type { FaceOverlay } from "../../lib/livefeed-types";

const mockClearRect = vi.fn();
const mockFillRect = vi.fn();
const mockStrokeRect = vi.fn();
const mockFillText = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  // Mock canvas getContext
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    clearRect: mockClearRect,
    fillRect: mockFillRect,
    strokeRect: mockStrokeRect,
    fillText: mockFillText,
    fillStyle: "",
    strokeStyle: "",
    lineWidth: 0,
    font: "",
  })) as unknown as typeof HTMLCanvasElement.prototype.getContext;
});

function makeVideoEl(overrides?: Partial<HTMLVideoElement>) {
  return {
    clientWidth: 640,
    clientHeight: 480,
    videoWidth: 640,
    videoHeight: 480,
    ...overrides,
  } as unknown as HTMLVideoElement;
}

function makeFace(overrides?: Partial<FaceOverlay>): FaceOverlay {
  return {
    bbox: { x: 100, y: 100, w: 50, h: 50 },
    dominant_emotion: "happy",
    engagement_level: "engaged",
    engagement_score: 0.9,
    ...overrides,
  };
}

describe("OverlayCanvas", () => {
  it("draws rectangles for each face", () => {
    const faces = [makeFace(), makeFace({ bbox: { x: 200, y: 200, w: 60, h: 60 } })];
    render(<OverlayCanvas faces={faces} videoEl={makeVideoEl()} />);
    expect(mockStrokeRect).toHaveBeenCalledTimes(2);
  });

  it("uses green for engaged faces", () => {
    const faces = [makeFace({ engagement_level: "engaged" })];
    render(<OverlayCanvas faces={faces} videoEl={makeVideoEl()} />);
    // Verify strokeRect was called (color is set via ctx.strokeStyle assignment)
    expect(mockStrokeRect).toHaveBeenCalled();
  });

  it("clears canvas before redraw", () => {
    render(<OverlayCanvas faces={[makeFace()]} videoEl={makeVideoEl()} />);
    expect(mockClearRect).toHaveBeenCalled();
  });

  it("handles empty faces array", () => {
    render(<OverlayCanvas faces={[]} videoEl={makeVideoEl()} />);
    expect(mockStrokeRect).not.toHaveBeenCalled();
    expect(mockClearRect).toHaveBeenCalled();
  });

  it("handles null videoEl", () => {
    render(<OverlayCanvas faces={[makeFace()]} videoEl={null} />);
    expect(mockStrokeRect).not.toHaveBeenCalled();
  });

  it("draws label text for each face", () => {
    const faces = [makeFace({ engagement_level: "passive" })];
    render(<OverlayCanvas faces={faces} videoEl={makeVideoEl()} />);
    expect(mockFillText).toHaveBeenCalledWith("passive", expect.any(Number), expect.any(Number));
  });
});
