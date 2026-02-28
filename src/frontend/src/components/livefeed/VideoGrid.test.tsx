import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import VideoGrid from "./VideoGrid";

// Mock CameraFeed to avoid HTMLVideoElement srcObject issues
vi.mock("./CameraFeed", () => ({
  default: ({ cameraId }: { cameraId: string }) => (
    <div data-testid={`camera-feed-${cameraId}`}>Feed: {cameraId}</div>
  ),
}));

afterEach(() => {
  cleanup();
});

function makeCameras(count: number) {
  const map = new Map<
    string,
    { stream: MediaStream | null; analysisResult?: undefined }
  >();
  for (let i = 1; i <= count; i++) {
    map.set(`cam-${i}`, { stream: null });
  }
  return map;
}

describe("VideoGrid", () => {
  it("0 cameras: shows empty state", () => {
    render(<VideoGrid cameras={new Map()} />);
    expect(
      screen.getByText("Waiting for cameras... 0/4 connected"),
    ).toBeDefined();
  });

  it("1 camera: renders single feed", () => {
    render(<VideoGrid cameras={makeCameras(1)} />);
    expect(screen.getByTestId("camera-feed-cam-1")).toBeDefined();
    expect(screen.queryByTestId("camera-feed-cam-2")).toBeNull();
  });

  it("2 cameras: renders 2 feeds", () => {
    render(<VideoGrid cameras={makeCameras(2)} />);
    expect(screen.getByTestId("camera-feed-cam-1")).toBeDefined();
    expect(screen.getByTestId("camera-feed-cam-2")).toBeDefined();
  });

  it("3 cameras: renders 3 feeds", () => {
    render(<VideoGrid cameras={makeCameras(3)} />);
    expect(screen.getByTestId("camera-feed-cam-1")).toBeDefined();
    expect(screen.getByTestId("camera-feed-cam-2")).toBeDefined();
    expect(screen.getByTestId("camera-feed-cam-3")).toBeDefined();
  });

  it("4 cameras: renders 2x2 grid", () => {
    const { container } = render(<VideoGrid cameras={makeCameras(4)} />);
    const grid = container.querySelector(".grid-cols-2");
    expect(grid).not.toBeNull();
    expect(screen.getByTestId("camera-feed-cam-1")).toBeDefined();
    expect(screen.getByTestId("camera-feed-cam-2")).toBeDefined();
    expect(screen.getByTestId("camera-feed-cam-3")).toBeDefined();
    expect(screen.getByTestId("camera-feed-cam-4")).toBeDefined();
  });

  it("camera removed: adjusts layout", () => {
    const cameras4 = makeCameras(4);
    const { rerender } = render(<VideoGrid cameras={cameras4} />);

    expect(screen.getByTestId("camera-feed-cam-4")).toBeDefined();

    const cameras3 = makeCameras(3);
    rerender(<VideoGrid cameras={cameras3} />);

    expect(screen.queryByTestId("camera-feed-cam-4")).toBeNull();
    expect(screen.getByTestId("camera-feed-cam-3")).toBeDefined();
  });
});
