import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import ScoreCard from "./ScoreCard";

describe("ScoreCard", () => {
  it("renders nothing when no result", () => {
    const { container } = render(<ScoreCard result={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders reward score", () => {
    render(<ScoreCard result={{ reward: 0.875, bridge_reward: 0.9, metrics_reward: 0.85 }} />);
    expect(screen.getByText("0.875")).toBeInTheDocument();
  });

  it("renders bridge and metrics scores", () => {
    render(<ScoreCard result={{ reward: 0.8, bridge_reward: 0.9, metrics_reward: 0.7, bridge_score: 7, metrics_score: 2 }} />);
    expect(screen.getByText("Bridge Score")).toBeInTheDocument();
    expect(screen.getByText("Metrics Score")).toBeInTheDocument();
  });
});
