import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import CustomInventory from "./CustomInventory.jsx";

describe("CustomInventory", () => {
  it("renders form and json tabs", () => {
    render(<CustomInventory onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Form")).toBeInTheDocument();
    expect(screen.getByText("JSON")).toBeInTheDocument();
  });

  it("renders Custom Inventory heading", () => {
    render(<CustomInventory onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Custom Inventory")).toBeInTheDocument();
  });

  it("renders shared settings", () => {
    render(<CustomInventory onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Horizon (days)")).toBeInTheDocument();
    expect(screen.getByText("Household")).toBeInTheDocument();
  });

  it("renders add item button in form mode", () => {
    render(<CustomInventory onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("+ Add item")).toBeInTheDocument();
  });

  it("renders Load Inventory button", () => {
    render(<CustomInventory onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByText("Load Inventory")).toBeInTheDocument();
  });
});
