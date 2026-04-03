import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import FridgeView from "./FridgeView.jsx";

const SAMPLE_INVENTORY = [
  { name: "chicken_breast", quantity: 500, unit: "g", expiry_date: "2026-01-03", category: "protein" },
  { name: "spinach", quantity: 200, unit: "g", expiry_date: "2026-01-02", category: "vegetable" },
  { name: "white_rice", quantity: 1000, unit: "g", expiry_date: "2026-01-10", category: "carb" },
  { name: "olive_oil", quantity: 500, unit: "ml", expiry_date: "2026-06-01", category: "condiment" },
];

describe("FridgeView", () => {
  it("renders all inventory items", () => {
    render(
      <FridgeView
        inventory={SAMPLE_INVENTORY}
        currentDate="2026-01-01"
        horizon={3}
        householdSize={2}
        restrictions={[]}
      />
    );
    expect(screen.getByText("chicken breast")).toBeInTheDocument();
    expect(screen.getByText("spinach")).toBeInTheDocument();
    expect(screen.getByText("white rice")).toBeInTheDocument();
    expect(screen.getByText("olive oil")).toBeInTheDocument();
  });

  it("displays item quantities with units", () => {
    render(
      <FridgeView
        inventory={SAMPLE_INVENTORY}
        currentDate="2026-01-01"
        horizon={3}
        householdSize={2}
        restrictions={[]}
      />
    );
    expect(screen.getByText("500g")).toBeInTheDocument();
    expect(screen.getByText("200g")).toBeInTheDocument();
    expect(screen.getByText("500ml")).toBeInTheDocument();
  });

  it("shows days until expiry", () => {
    render(
      <FridgeView
        inventory={SAMPLE_INVENTORY}
        currentDate="2026-01-01"
        horizon={3}
        householdSize={2}
        restrictions={[]}
      />
    );
    expect(screen.getByText("2 days")).toBeInTheDocument(); // chicken
    expect(screen.getByText("1 day")).toBeInTheDocument();  // spinach
  });

  it("displays metadata tags", () => {
    render(
      <FridgeView
        inventory={SAMPLE_INVENTORY}
        currentDate="2026-01-01"
        horizon={3}
        householdSize={2}
        restrictions={["vegetarian"]}
      />
    );
    expect(screen.getByText("4")).toBeInTheDocument(); // items count
    expect(screen.getByText("3d")).toBeInTheDocument(); // horizon
    expect(screen.getByText("vegetarian")).toBeInTheDocument();
  });

  it("renders with empty restrictions", () => {
    render(
      <FridgeView
        inventory={SAMPLE_INVENTORY}
        currentDate="2026-01-01"
        horizon={7}
        householdSize={3}
        restrictions={[]}
      />
    );
    expect(screen.getByText("Fridge Inventory")).toBeInTheDocument();
    expect(screen.queryByText("Restrictions")).not.toBeInTheDocument();
  });

  it("renders with empty inventory", () => {
    render(
      <FridgeView
        inventory={[]}
        currentDate="2026-01-01"
        horizon={3}
        householdSize={2}
        restrictions={[]}
      />
    );
    expect(screen.getByText("Fridge Inventory")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument(); // 0 items
  });
});
