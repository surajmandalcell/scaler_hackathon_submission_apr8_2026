import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App.jsx";

describe("App", () => {
  it("renders the title", () => {
    render(<App />);
    expect(screen.getByText("FridgeEnv")).toBeInTheDocument();
  });

  it("renders difficulty buttons", () => {
    render(<App />);
    expect(screen.getByText("Easy")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Hard")).toBeInTheDocument();
  });

  it("renders the Reset button", () => {
    render(<App />);
    const buttons = screen.getAllByText("Reset");
    expect(buttons.length).toBeGreaterThanOrEqual(1);
    // The actual button (not the <strong> in help text)
    const btn = buttons.find((el) => el.tagName === "BUTTON");
    expect(btn).toBeInTheDocument();
  });

  it("shows empty state initially", () => {
    render(<App />);
    expect(screen.getByText(/Select a difficulty/)).toBeInTheDocument();
  });

  it("renders seed input with default value", () => {
    render(<App />);
    const seedInput = screen.getByDisplayValue("42");
    expect(seedInput).toBeInTheDocument();
  });

  it("renders the footer", () => {
    render(<App />);
    expect(screen.getByText(/Scaler x Meta/)).toBeInTheDocument();
  });
});
