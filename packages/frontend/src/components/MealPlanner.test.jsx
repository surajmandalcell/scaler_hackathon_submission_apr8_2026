import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import MealPlanner from "./MealPlanner.jsx";

const OBS = {
  inventory: [
    { name: "chicken_breast", quantity: 500, unit: "g", expiry_date: "2026-01-05", category: "protein" },
    { name: "white_rice", quantity: 1000, unit: "g", expiry_date: "2026-01-10", category: "carb" },
  ],
  horizon: 3,
  current_date: "2026-01-01",
  household_size: 2,
  dietary_restrictions: [],
};

describe("MealPlanner", () => {
  it("renders heading", () => {
    render(<MealPlanner observation={OBS} onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Meal Planner")).toBeInTheDocument();
  });

  it("renders day sections for horizon", () => {
    render(<MealPlanner observation={OBS} onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Day 1")).toBeInTheDocument();
    expect(screen.getByText("Day 2")).toBeInTheDocument();
    expect(screen.getByText("Day 3")).toBeInTheDocument();
  });

  it("renders submit button", () => {
    render(<MealPlanner observation={OBS} onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Submit Plan")).toBeInTheDocument();
  });

  it("renders ingredient dropdowns with items", () => {
    render(<MealPlanner observation={OBS} onSubmit={vi.fn()} loading={false} />);
    // Select elements should have the inventory items as options
    const selects = screen.getAllByRole("combobox");
    expect(selects.length).toBeGreaterThanOrEqual(3); // one per day at minimum
  });

  it("renders add ingredient buttons", () => {
    render(<MealPlanner observation={OBS} onSubmit={vi.fn()} loading={false} />);
    const addBtns = screen.getAllByText("+ ingredient");
    expect(addBtns.length).toBe(3); // one per day
  });
});
