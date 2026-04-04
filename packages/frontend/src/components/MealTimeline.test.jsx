import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MealTimeline from "./MealTimeline.jsx";

describe("MealTimeline", () => {
  it("renders heading", () => {
    render(<MealTimeline consumptionLog={{ a: 250 }} nutritionLog={{}} horizon={3} expiryEvents={[]} />);
    expect(screen.getByText("Daily Nutrition")).toBeInTheDocument();
  });

  it("shows consumed items", () => {
    render(<MealTimeline consumptionLog={{ chicken_breast: 250.5, white_rice: 300 }} nutritionLog={{}} horizon={3} expiryEvents={[]} />);
    expect(screen.getByText("chicken breast")).toBeInTheDocument();
    expect(screen.getByText("white rice")).toBeInTheDocument();
    expect(screen.getByText("250.5")).toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();
  });

  it("renders day columns", () => {
    render(<MealTimeline consumptionLog={{ a: 1 }} nutritionLog={{}} horizon={5} expiryEvents={[]} />);
    // Day numbers appear in the nutrition grid
    expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows wasted items", () => {
    render(<MealTimeline consumptionLog={{ chicken: 100 }} nutritionLog={{}} horizon={3} expiryEvents={["spinach", "tomatoes"]} />);
    expect(screen.getByText(/Wasted/)).toBeInTheDocument();
    expect(screen.getByText("spinach")).toBeInTheDocument();
    expect(screen.getByText("tomatoes")).toBeInTheDocument();
  });

  it("hides wasted when items were consumed", () => {
    render(<MealTimeline consumptionLog={{ spinach: 50 }} nutritionLog={{}} horizon={3} expiryEvents={["spinach"]} />);
    // spinach was consumed, so no "fully wasted" section
    expect(screen.queryByText(/Wasted/)).not.toBeInTheDocument();
  });

  it("returns null without data", () => {
    const { container } = render(<MealTimeline consumptionLog={null} nutritionLog={{}} horizon={3} expiryEvents={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("shows item count", () => {
    render(<MealTimeline consumptionLog={{ a: 10, b: 20, c: 30 }} nutritionLog={{}} horizon={3} expiryEvents={[]} />);
    expect(screen.getByText(/Consumption \(3 items\)/)).toBeInTheDocument();
  });

  it("shows nutrition legend", () => {
    render(<MealTimeline consumptionLog={{ a: 1 }} nutritionLog={{}} horizon={3} expiryEvents={[]} />);
    expect(screen.getByText(/P \/ C \/ V/)).toBeInTheDocument();
  });
});
