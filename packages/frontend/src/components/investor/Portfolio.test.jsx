import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import Portfolio from "./Portfolio.jsx";

const HARD_SCENARIO = {
  taskId: "hard",
  portfolio: {
    alpha: {
      fund_name: "RE Alpha Fund I",
      beginning_nav: 300.0,
      ending_nav: 338.0,
      moic: 2.15,
      irr: 0.184,
    },
    beta: {
      fund_name: "RE Beta Fund II",
      beginning_nav: 500.0,
      ending_nav: 520.0,
      moic: 1.3,
      irr: 0.09,
    },
  },
};

describe("Portfolio (investor)", () => {
  it("shows an empty state when no scenario is loaded", () => {
    render(<Portfolio scenario={null} taskId="easy" />);
    expect(screen.getByText(/No scenario loaded/i)).toBeInTheDocument();
  });

  it("renders fund rows with plain-English labels on hard mode", () => {
    render(<Portfolio scenario={HARD_SCENARIO} taskId="hard" />);

    // Fund names
    expect(screen.getByText("RE Alpha Fund I")).toBeInTheDocument();
    expect(screen.getByText("RE Beta Fund II")).toBeInTheDocument();

    // Alpha: MOIC 2.15 → "Good return" bucket, IRR 18.4% → "Good annual return"
    expect(screen.getByText(/2\.15x.*Good return/)).toBeInTheDocument();
    expect(screen.getByText(/18\.4%.*Good annual return/)).toBeInTheDocument();

    // Beta: MOIC 1.30 → "Capital returned, limited gain", IRR 9% → "In line with market"
    expect(screen.getByText(/1\.30x.*Capital returned, limited gain/)).toBeInTheDocument();
    expect(screen.getByText(/9\.0%.*In line with market/)).toBeInTheDocument();
  });

  it("hides MOIC/IRR with 'not available' copy on easy mode", () => {
    render(<Portfolio scenario={HARD_SCENARIO} taskId="easy" />);
    const notAvailableMoic = screen.getAllByText(/available in Medium mode and above/);
    const notAvailableIrr = screen.getAllByText(/available in Hard mode and above/);
    // Both funds show both "not available" rows
    expect(notAvailableMoic.length).toBe(2);
    expect(notAvailableIrr.length).toBe(2);
  });

  it("shows the mode banner for the current task", () => {
    render(<Portfolio scenario={HARD_SCENARIO} taskId="hard" />);
    expect(screen.getByText(/HARD MODE/)).toBeInTheDocument();
    expect(screen.getByText(/NAV Bridge \+ MOIC \+ IRR/)).toBeInTheDocument();
  });
});
