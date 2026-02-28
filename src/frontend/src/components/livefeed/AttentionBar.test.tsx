import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AttentionBar from "./AttentionBar";
import type { CollectiveAttention } from "../../lib/livefeed-types";

function makeAttention(
  overrides?: Partial<CollectiveAttention>,
): CollectiveAttention {
  return {
    score: 0.73,
    totalFaces: 18,
    activeCameras: 3,
    maxCameras: 4,
    ...overrides,
  };
}

describe("AttentionBar", () => {
  it("shows percentage", () => {
    render(<AttentionBar attention={makeAttention({ score: 0.73 })} />);
    expect(screen.getByText("Attention: 73%")).toBeDefined();
  });

  it("shows camera count", () => {
    render(
      <AttentionBar attention={makeAttention({ activeCameras: 3 })} />,
    );
    expect(screen.getAllByText(/3\/4 streams active/).length).toBeGreaterThan(0);
  });

  it("shows face count", () => {
    render(
      <AttentionBar attention={makeAttention({ totalFaces: 18 })} />,
    );
    expect(screen.getAllByText(/18 faces detected/).length).toBeGreaterThan(0);
  });

  it("shows green bar for high attention", () => {
    const { container } = render(
      <AttentionBar attention={makeAttention({ score: 0.8 })} />,
    );
    const bar = container.querySelector(".bg-green-500");
    expect(bar).not.toBeNull();
  });

  it("shows red bar for low attention", () => {
    const { container } = render(
      <AttentionBar attention={makeAttention({ score: 0.1 })} />,
    );
    const bar = container.querySelector(".bg-red-500");
    expect(bar).not.toBeNull();
  });

  it("shows yellow bar for medium attention", () => {
    const { container } = render(
      <AttentionBar attention={makeAttention({ score: 0.45 })} />,
    );
    const bar = container.querySelector(".bg-yellow-500");
    expect(bar).not.toBeNull();
  });

  it("shows 0% with no data", () => {
    render(
      <AttentionBar
        attention={makeAttention({
          score: 0,
          totalFaces: 0,
          activeCameras: 0,
        })}
      />,
    );
    expect(screen.getByText("Attention: 0%")).toBeDefined();
    expect(screen.getAllByText(/0 faces detected/).length).toBeGreaterThan(0);
  });
});
