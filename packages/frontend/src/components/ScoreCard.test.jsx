import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ScoreCard from "./ScoreCard.jsx";

const GOOD_REWARD = {
  score: 0.85,
  waste_rate: 0.15,
  nutrition_score: 0.67,
  items_used: 6,
  items_expired: 1,
  violations: [],
};

const BAD_REWARD = {
  score: 0.2,
  waste_rate: 0.8,
  nutrition_score: 0.0,
  items_used: 1,
  items_expired: 5,
  violations: [
    "Day 1: chicken_breast violates vegetarian",
    "Day 2: ground_beef violates vegetarian",
  ],
};

describe("ScoreCard", () => {
  it("renders the grader score as percentage", () => {
    render(<ScoreCard reward={GOOD_REWARD} info={{}} />);
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("displays waste rate", () => {
    render(<ScoreCard reward={GOOD_REWARD} info={{}} />);
    expect(screen.getByText("15%")).toBeInTheDocument(); // waste
  });

  it("displays nutrition score", () => {
    render(<ScoreCard reward={GOOD_REWARD} info={{}} />);
    expect(screen.getByText("67%")).toBeInTheDocument(); // nutrition
  });

  it("displays items used and expired counts", () => {
    render(<ScoreCard reward={GOOD_REWARD} info={{}} />);
    expect(screen.getByText("6")).toBeInTheDocument(); // items used
    expect(screen.getByText("1")).toBeInTheDocument(); // items expired
  });

  it("shows violations when present", () => {
    render(<ScoreCard reward={BAD_REWARD} info={{}} />);
    expect(screen.getByText(/Violations \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/chicken_breast violates vegetarian/)).toBeInTheDocument();
    expect(screen.getByText(/ground_beef violates vegetarian/)).toBeInTheDocument();
  });

  it("hides violations section when none", () => {
    render(<ScoreCard reward={GOOD_REWARD} info={{}} />);
    expect(screen.queryByText(/Violations/)).not.toBeInTheDocument();
  });

  it("returns null when no reward", () => {
    const { container } = render(<ScoreCard reward={null} info={{}} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders low score correctly", () => {
    render(<ScoreCard reward={BAD_REWARD} info={{}} />);
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("80%")).toBeInTheDocument(); // waste rate
  });
});
