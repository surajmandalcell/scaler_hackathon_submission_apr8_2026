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
    expect(screen.getByText("Custom")).toBeInTheDocument();
  });

  it("renders the Generate button", () => {
    render(<App />);
    expect(screen.getByText("Generate")).toBeInTheDocument();
  });

  it("shows empty state initially", () => {
    render(<App />);
    expect(screen.getByText(/generate a fridge/i)).toBeInTheDocument();
  });

  it("renders seed input with default value", () => {
    render(<App />);
    expect(screen.getByDisplayValue("42")).toBeInTheDocument();
  });

  it("has docs button", () => {
    render(<App />);
    expect(screen.getByText("Docs")).toBeInTheDocument();
  });
});
