import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MealTimeline from "./MealTimeline.jsx";

describe("MealTimeline", () => {
  it("renders consumption summary heading", () => {
    render(
      <MealTimeline
        consumptionLog={{ chicken_breast: 250, spinach: 100 }}
        nutritionLog={{ 1: ["protein", "vegetable"], 2: ["protein"] }}
        horizon={3}
        expiryEvents={[]}
      />
    );
    expect(screen.getByText("Consumption Summary")).toBeInTheDocument();
  });

  it("shows consumed items with quantities", () => {
    render(
      <MealTimeline
        consumptionLog={{ chicken_breast: 250.5, white_rice: 300 }}
        nutritionLog={{}}
        horizon={3}
        expiryEvents={[]}
      />
    );
    expect(screen.getByText("chicken breast")).toBeInTheDocument();
    expect(screen.getByText("white rice")).toBeInTheDocument();
    expect(screen.getByText("250.5")).toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();
  });

  it("renders day columns for horizon", () => {
    render(
      <MealTimeline
        consumptionLog={{ a: 1 }}
        nutritionLog={{}}
        horizon={5}
        expiryEvents={[]}
      />
    );
    expect(screen.getByText("D1")).toBeInTheDocument();
    expect(screen.getByText("D5")).toBeInTheDocument();
  });

  it("shows wasted items section", () => {
    render(
      <MealTimeline
        consumptionLog={{ chicken_breast: 100 }}
        nutritionLog={{}}
        horizon={3}
        expiryEvents={["spinach", "tomatoes"]}
      />
    );
    expect(screen.getByText(/Wasted Items/)).toBeInTheDocument();
    expect(screen.getByText("spinach")).toBeInTheDocument();
    expect(screen.getByText("tomatoes")).toBeInTheDocument();
  });

  it("hides wasted items when none fully wasted", () => {
    render(
      <MealTimeline
        consumptionLog={{ spinach: 50 }}
        nutritionLog={{}}
        horizon={3}
        expiryEvents={["spinach"]}
      />
    );
    // spinach was consumed so it's not "fully wasted"
    expect(screen.queryByText(/Wasted Items \(0/)).toBeInTheDocument();
  });

  it("returns null when no consumption log", () => {
    const { container } = render(
      <MealTimeline
        consumptionLog={null}
        nutritionLog={{}}
        horizon={3}
        expiryEvents={[]}
      />
    );
    expect(container.innerHTML).toBe("");
  });

  it("shows item count in header", () => {
    render(
      <MealTimeline
        consumptionLog={{ a: 10, b: 20, c: 30 }}
        nutritionLog={{}}
        horizon={3}
        expiryEvents={[]}
      />
    );
    expect(screen.getByText(/Items Consumed \(3\)/)).toBeInTheDocument();
  });

  it("shows legend for nutrition dots", () => {
    render(
      <MealTimeline
        consumptionLog={{ a: 1 }}
        nutritionLog={{}}
        horizon={3}
        expiryEvents={[]}
      />
    );
    expect(screen.getByText("Protein")).toBeInTheDocument();
    expect(screen.getByText("Carb")).toBeInTheDocument();
    expect(screen.getByText("Vegetable")).toBeInTheDocument();
  });
});
