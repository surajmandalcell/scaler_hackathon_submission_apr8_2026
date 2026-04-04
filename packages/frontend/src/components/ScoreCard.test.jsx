import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ScoreCard from "./ScoreCard.jsx";

const GOOD = {
  score: 0.85, waste_rate: 0.15, nutrition_score: 0.67,
  items_used: 6, items_expired: 1, violations: [],
};

const BAD = {
  score: 0.2, waste_rate: 0.8, nutrition_score: 0.0,
  items_used: 1, items_expired: 5,
  violations: ["Day 1: chicken violates vegetarian", "Day 2: beef violates vegetarian"],
};

describe("ScoreCard", () => {
  it("renders score as percentage", () => {
    render(<ScoreCard reward={GOOD} />);
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("displays waste rate", () => {
    render(<ScoreCard reward={GOOD} />);
    expect(screen.getByText("15%")).toBeInTheDocument();
  });

  it("displays nutrition score", () => {
    render(<ScoreCard reward={GOOD} />);
    expect(screen.getByText("67%")).toBeInTheDocument();
  });

  it("displays items used and expired", () => {
    render(<ScoreCard reward={GOOD} />);
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("shows violations when present", () => {
    render(<ScoreCard reward={BAD} />);
    expect(screen.getByText(/2 violations/)).toBeInTheDocument();
    expect(screen.getByText(/chicken violates vegetarian/)).toBeInTheDocument();
  });

  it("hides violations when none", () => {
    render(<ScoreCard reward={GOOD} />);
    expect(screen.queryByText(/violation/i)).not.toBeInTheDocument();
  });

  it("returns null without reward", () => {
    const { container } = render(<ScoreCard reward={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders low score", () => {
    render(<ScoreCard reward={BAD} />);
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("80%")).toBeInTheDocument();
  });
});
