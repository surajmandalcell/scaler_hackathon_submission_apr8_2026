import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import DocsPage from "./DocsPage.jsx";

describe("DocsPage", () => {
  it("renders main sections", () => {
    render(<DocsPage />);
    expect(screen.getByText("What is FridgeEnv")).toBeInTheDocument();
    expect(screen.getByText("API Reference")).toBeInTheDocument();
    expect(screen.getByText("Data Models")).toBeInTheDocument();
    expect(screen.getByText("Difficulty Levels")).toBeInTheDocument();
    expect(screen.getByText("Baseline Scores")).toBeInTheDocument();
  });

  it("renders API endpoints", () => {
    render(<DocsPage />);
    expect(screen.getByText("/health")).toBeInTheDocument();
    expect(screen.getByText("/reset")).toBeInTheDocument();
    expect(screen.getByText("/step")).toBeInTheDocument();
    expect(screen.getByText("/state")).toBeInTheDocument();
  });

  it("renders data model names", () => {
    render(<DocsPage />);
    expect(screen.getByText("Observation")).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Reward")).toBeInTheDocument();
  });
});
