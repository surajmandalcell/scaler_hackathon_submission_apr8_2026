import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Dashboard from "./Dashboard";

describe("Dashboard", () => {
  it("renders difficulty buttons", () => {
    render(
      <Dashboard taskId="easy" setTaskId={() => {}} scenario={null} loading={false} onLoadScenario={() => {}} />
    );
    expect(screen.getByText("Easy")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Hard")).toBeInTheDocument();
  });

  it("renders load button", () => {
    render(
      <Dashboard taskId="easy" setTaskId={() => {}} scenario={null} loading={false} onLoadScenario={() => {}} />
    );
    expect(screen.getByText("Load Scenario")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(
      <Dashboard taskId="easy" setTaskId={() => {}} scenario={null} loading={true} onLoadScenario={() => {}} />
    );
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows fund cards when scenario provided", () => {
    const scenario = {
      taskId: "easy",
      portfolio: {
        alpha: { fund_name: "RE Alpha Fund I", beginning_nav: 100, ending_nav: 120, moic: 1.5, irr: 0.12 },
      },
    };
    render(
      <Dashboard taskId="easy" setTaskId={() => {}} scenario={scenario} loading={false} onLoadScenario={() => {}} />
    );
    expect(screen.getByText("RE Alpha Fund I")).toBeInTheDocument();
  });

  it("hides MOIC for easy difficulty", () => {
    const scenario = {
      taskId: "easy",
      portfolio: {
        alpha: { fund_name: "Alpha", beginning_nav: 100, ending_nav: 120, moic: 1.5, irr: 0.12 },
      },
    };
    render(
      <Dashboard taskId="easy" setTaskId={() => {}} scenario={scenario} loading={false} onLoadScenario={() => {}} />
    );
    expect(screen.queryByText("MOIC")).not.toBeInTheDocument();
  });

  it("shows MOIC for medium difficulty", () => {
    const scenario = {
      taskId: "medium",
      portfolio: {
        beta: { fund_name: "Beta", beginning_nav: 200, ending_nav: 240, moic: 1.8, irr: 0.15 },
      },
    };
    render(
      <Dashboard taskId="medium" setTaskId={() => {}} scenario={scenario} loading={false} onLoadScenario={() => {}} />
    );
    expect(screen.getByText("MOIC")).toBeInTheDocument();
  });

  it("shows IRR only for hard difficulty", () => {
    const scenario = {
      taskId: "hard",
      portfolio: {
        gamma: { fund_name: "Gamma", beginning_nav: 300, ending_nav: 360, moic: 2.0, irr: 0.20 },
      },
    };
    render(
      <Dashboard taskId="hard" setTaskId={() => {}} scenario={scenario} loading={false} onLoadScenario={() => {}} />
    );
    expect(screen.getByText("IRR")).toBeInTheDocument();
  });
});
