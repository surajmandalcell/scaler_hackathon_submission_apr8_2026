import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Playground from "./Playground.jsx";

const MOCK_TOOLS = [
  {
    name: "get_nav_bridge",
    description: "8-line NAV bridge for a fund (USD millions).",
    parameters: {
      type: "object",
      properties: { fund_id: { type: "string" } },
      required: ["fund_id"],
    },
  },
  {
    name: "get_portfolio_summary",
    description: "Fund-level ending NAV, MOIC, and IRR.",
    parameters: {
      type: "object",
      properties: { funds: { type: "array", items: { type: "string" } } },
      required: [],
    },
  },
  {
    name: "submit_report",
    description: "Grade submission.",
    parameters: {
      type: "object",
      properties: {
        nav_bridge: { type: "object" },
        metrics: { type: "object" },
      },
      required: ["nav_bridge"],
    },
  },
];

const MOCK_STATE = {
  task_id: "easy",
  is_done: false,
  step_count: 0,
  funds_loaded: ["alpha"],
  deals_loaded: ["embassy_office"],
};

beforeEach(() => {
  global.fetch = vi.fn((url) => {
    if (typeof url === "string" && url.includes("/api/session/tools")) {
      return Promise.resolve({ json: () => Promise.resolve({ tools: MOCK_TOOLS }) });
    }
    if (typeof url === "string" && url.includes("/api/session/state")) {
      return Promise.resolve({ json: () => Promise.resolve(MOCK_STATE) });
    }
    return Promise.resolve({ json: () => Promise.resolve({}) });
  });
});

describe("Playground", () => {
  it("renders the tool catalogue from /api/session/tools", async () => {
    render(<Playground />);

    // Headline is always visible
    expect(screen.getByText(/MCP Playground/)).toBeInTheDocument();

    // Wait for the async fetch to populate the list -- tool names can appear
    // in both the ToolList card and the ToolForm heading (when selected), so
    // use getAllByText to tolerate >1 match.
    await waitFor(() => {
      expect(screen.getAllByText("get_nav_bridge").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("get_portfolio_summary").length).toBeGreaterThan(0);
    expect(screen.getAllByText("submit_report").length).toBeGreaterThan(0);
  });

  it("shows session state metrics (task_id, funds loaded, call count)", async () => {
    render(<Playground />);

    await waitFor(() => {
      expect(screen.getByText(/task_id/)).toBeInTheDocument();
    });

    // task_id value should be present
    expect(screen.getByText("easy")).toBeInTheDocument();
    // "calls this session" metric label renders
    expect(screen.getByText(/calls this session/)).toBeInTheDocument();
  });

  it("renders the form for the first selected tool with required parameters", async () => {
    render(<Playground />);
    await waitFor(() => {
      expect(screen.getAllByText("get_nav_bridge").length).toBeGreaterThan(0);
    });
    // The selected tool's form must show its fund_id field label
    await waitFor(() => {
      const labels = screen.getAllByText(/fund_id/);
      expect(labels.length).toBeGreaterThan(0);
    });
    // "Call tool" submit button should exist
    expect(screen.getByRole("button", { name: /Call tool/i })).toBeInTheDocument();
  });
});
