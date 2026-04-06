"""
Inference Script — FundLens Baseline Agent
==========================================
Environment variables required:
  API_BASE_URL   LLM endpoint (default: HuggingFace router)
  MODEL_NAME     Model identifier
  HF_TOKEN       API key / HuggingFace token

Run:
  python inference.py
"""
import os
import json
import textwrap
from openai import OpenAI
from openenv.core.env_server import CallToolAction
from fundlens.server.environment import FundLensEnvironment

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "no-key")
MODEL_NAME   = os.getenv("MODEL_NAME", "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF")
MAX_STEPS    = 8
TEMPERATURE  = 0.1
MAX_TOKENS   = 1500

SYSTEM_PROMPT = textwrap.dedent("""
    You are a PE fund analyst using the FundLens reporting platform.
    Use MCP tools to compute NAV bridges and performance metrics for the fund.

    Available tools:
    - get_available_filters() — discover fund_ids, deal_ids, sectors
    - get_portfolio_summary(funds) — MOIC, DPI, RVPI, TVPI, IRR per fund
    - get_nav_bridge(fund_id) — 12-line NAV walk in USD millions
    - get_irr(fund_id, irr_type) — IRR: "pre_fx" | "post_fx" | "both"
    - compare_funds(funds, metrics) — side-by-side fund comparison
    - get_sector_report(sector, funds) — breakdown by property sector
    - get_deal_exposure(deal_id) — cross-fund consolidation for a deal
    - submit_report(nav_bridge, metrics) — SUBMIT AND GRADE YOUR WORK

    Workflow:
    1. get_available_filters() → identify which fund to analyze
    2. get_nav_bridge(fund_id) → get the 12-line NAV bridge
    3. get_portfolio_summary(funds) → get MOIC/DPI/RVPI/TVPI
    4. get_irr(fund_id, "both") → get IRR values
    5. submit_report(nav_bridge, metrics) → done

    NAV Bridge keys: beginning_nav, contribution, roc, gl_on_investment,
    gl_of_fx, current_income, cashflow_adjusted_nav, income_reversal,
    debt_mtm, write_up_down, ending_nav

    Metrics keys: moic, dpi, rvpi, tvpi, irr_post_fx, irr_pre_fx, fx_attribution

    Respond ONLY with a JSON object (no markdown, no prose):
    {
      "tool": "tool_name",
      "arguments": {"param": "value"}
    }
""").strip()


def call_llm(client: OpenAI, messages: list) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        print(f"  [LLM error: {exc}]")
        return ""


def parse_tool_call(text: str) -> dict | None:
    """Extract first JSON object from LLM response."""
    text = text.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def run_task(env: FundLensEnvironment, client: OpenAI, task_id: str) -> float:
    print(f"\n{'='*60}")
    print(f"  Task: {task_id.upper()}")
    print(f"{'='*60}")

    obs = env.reset(task_id=task_id)
    print(f"  Raj asks: {obs.task_description}")
    print(f"  Funds in scope: {obs.available_funds}")
    print(f"  Portfolio NAV: ${obs.portfolio_nav_usd:.2f}M")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Task: {obs.task_description}\n"
            f"Funds available: {obs.available_funds}\n"
            f"Portfolio NAV: ${obs.portfolio_nav_usd:.2f}M\n\n"
            "Start by calling get_available_filters() to confirm what data is loaded."
        )},
    ]

    nav_bridge_cache: dict = {}
    metrics_cache: dict = {}
    reward = 0.0

    for step in range(1, MAX_STEPS + 1):
        print(f"\n  Step {step}/{MAX_STEPS}")

        if env.state.is_done:
            break

        response = call_llm(client, messages)
        print(f"  LLM: {response[:300]}")

        tool_call = parse_tool_call(response)
        if not tool_call:
            print("  Could not parse tool call. Prompting again.")
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "Please respond with a valid JSON tool call."})
            continue

        tool_name = tool_call.get("tool", "")
        arguments = tool_call.get("arguments", {})
        print(f"  Calling: {tool_name}({json.dumps(arguments)[:120]})")

        step_obs = env.step(CallToolAction(tool_name=tool_name, arguments=arguments))
        result = step_obs.result.data if step_obs.result else None
        result_str = json.dumps(result, indent=2)[:600] if result else str(step_obs.error)
        print(f"  Result: {result_str[:300]}")

        # Cache bridge and metrics so we can auto-submit if LLM forgets
        if tool_name == "get_nav_bridge" and isinstance(result, dict) and "ending_nav" in result:
            nav_bridge_cache = result
        if tool_name in ("get_portfolio_summary", "get_irr") and isinstance(result, dict):
            # Flatten fund-level data into flat metrics dict
            for v in result.values():
                if isinstance(v, dict):
                    metrics_cache.update(v)
                else:
                    metrics_cache.update(result)
                    break

        # Check if reward came back (submit_report was called)
        if isinstance(result, dict) and "reward" in result:
            reward = result["reward"]
            print(f"\n  REWARD: {reward:.4f}")
            print(f"  Bridge score: {result.get('bridge_score', '?')}")
            print(f"  Metrics score: {result.get('metrics_score', '?')}")
            break

        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": (
                f"Tool result for {tool_name}:\n{result_str}\n\n"
                "Continue. Call the next tool, or call submit_report() if you have "
                "nav_bridge and metrics values ready."
            ),
        })

    else:
        # Max steps reached — auto-submit with cached values if available
        if nav_bridge_cache or metrics_cache:
            print("\n  Max steps reached. Auto-submitting cached values.")
            sub_obs = env.step(CallToolAction(
                tool_name="submit_report",
                arguments={"nav_bridge": nav_bridge_cache, "metrics": metrics_cache},
            ))
            result = sub_obs.result.data if sub_obs.result else {}
            reward = result.get("reward", 0.0) if isinstance(result, dict) else 0.0
            print(f"  Auto-submit REWARD: {reward:.4f}")

    return reward


def main() -> None:
    if API_KEY == "no-key":
        raise EnvironmentError(
            "No API key found. Set HF_TOKEN or API_KEY environment variable.\n"
            "Example: export HF_TOKEN=hf_..."
        )
    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = FundLensEnvironment()

    results: dict[str, float] = {}
    for task_id in ["easy", "medium", "hard"]:
        results[task_id] = run_task(env, llm_client, task_id)

    print(f"\n{'='*60}")
    print("  FINAL RESULTS")
    print(f"{'='*60}")
    for task_id, r in results.items():
        print(f"  {task_id:8s}: {r:.4f}")
    avg = sum(results.values()) / len(results)
    print(f"  {'average':8s}: {avg:.4f}")


if __name__ == "__main__":
    main()
