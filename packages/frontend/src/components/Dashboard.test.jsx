import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Dashboard from "./Dashboard";

const baseProps = {
  taskId: "easy",
  setTaskId: () => {},
  scenario: null,
  loading: false,
  loadError: null,
  onLoadScenario: () => {},
};

describe("Dashboard", () => {
  it("renders difficulty chips", () => {
    render(<Dashboard {...baseProps} />);
    expect(screen.getByRole("button", { name: "Easy" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Medium" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hard" })).toBeInTheDocument();
  });

  it("renders the load scenario button", () => {
    render(<Dashboard {...baseProps} />);
    expect(
      screen.getByRole("button", { name: /load scenario/i })
    ).toBeInTheDocument();
  });

  it("shows loading state on the button", () => {
    render(<Dashboard {...baseProps} loading={true} />);
    expect(screen.getByRole("button", { name: /loading/i })).toBeInTheDocument();
  });

  it("renders fund cards when a scenario is provided", () => {
    const scenario = {
      taskId: "easy",
      portfolio: {
        alpha: {
          fund_name: "RE Alpha Fund I",
          beginning_nav: 100,
          ending_nav: 120,
          moic: 1.5,
          irr: 0.12,
        },
      },
    };
    render(<Dashboard {...baseProps} scenario={scenario} />);
    expect(screen.getByText("RE Alpha Fund I")).toBeInTheDocument();
  });

  it("hides MOIC and IRR for easy difficulty", () => {
    const scenario = {
      taskId: "easy",
      portfolio: {
        alpha: {
          fund_name: "Alpha",
          beginning_nav: 100,
          ending_nav: 120,
          moic: 1.5,
          irr: 0.12,
        },
      },
    };
    render(<Dashboard {...baseProps} scenario={scenario} />);
    expect(screen.queryByText("MOIC")).not.toBeInTheDocument();
    expect(screen.queryByText("IRR")).not.toBeInTheDocument();
  });

  it("shows MOIC for medium difficulty", () => {
    const scenario = {
      taskId: "medium",
      portfolio: {
        beta: {
          fund_name: "Beta",
          beginning_nav: 200,
          ending_nav: 240,
          moic: 1.8,
          irr: 0.15,
        },
      },
    };
    render(<Dashboard {...baseProps} taskId="medium" scenario={scenario} />);
    expect(screen.getByText("MOIC")).toBeInTheDocument();
    expect(screen.queryByText("IRR")).not.toBeInTheDocument();
  });

  it("shows IRR only for hard difficulty", () => {
    const scenario = {
      taskId: "hard",
      portfolio: {
        gamma: {
          fund_name: "Gamma",
          beginning_nav: 300,
          ending_nav: 360,
          moic: 2.0,
          irr: 0.2,
        },
      },
    };
    render(<Dashboard {...baseProps} taskId="hard" scenario={scenario} />);
    expect(screen.getByText("MOIC")).toBeInTheDocument();
    expect(screen.getByText("IRR")).toBeInTheDocument();
  });
});
