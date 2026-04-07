import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import NAVBridge from "./NAVBridge";

describe("NAVBridge", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("shows empty state when no scenario", () => {
    render(<NAVBridge scenario={null} />);
    expect(screen.getByText(/Load a scenario/i)).toBeInTheDocument();
  });

  it("renders bridge rows when data loaded", async () => {
    global.fetch.mockResolvedValue({
      json: async () => ({
        beginning_nav: 100,
        contribution: 20,
        disposition: 5,
        income: 3,
        cashflow_adjusted_nav: 118,
        income_reversal: -3,
        write_up_down: 5,
        ending_nav: 120,
      }),
    });

    const scenario = {
      taskId: "easy",
      portfolio: { alpha: { fund_name: "Alpha Fund", beginning_nav: 100, ending_nav: 120 } },
    };

    render(<NAVBridge scenario={scenario} />);

    await waitFor(() => {
      expect(screen.getByText("Opening Value")).toBeInTheDocument();
      expect(screen.getByText("= Closing Value")).toBeInTheDocument();
    });
  });
});
