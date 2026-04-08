"""
FundLens — Baseline Inference Script
====================================
Required environment variables:
    API_BASE_URL      LLM endpoint (default: https://router.huggingface.co/v1)
    MODEL_NAME        Model identifier (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN          Hugging Face / API key (NO default — must be set)
    LOCAL_IMAGE_NAME  Local Docker image for the env (default: fundlens:latest)

This script follows the structured-stdout contract from the hackathon
sample inference script:

    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

It runs all three FundLens difficulty tasks (easy / medium / hard) in
sequence, each as its own episode with its own [START]/[STEP]/[END]
block, then prints a final aggregate line.

Baseline strategy is deterministic on purpose (the grader runs inside
the environment and exposes pre-computed correct values through the
MCP tool surface -- the baseline's job is just to fetch the right
tools in the right order, which is the behaviour we want to measure
the framework on). The LLM is still invoked once per episode through
the OpenAI client to produce a strategy summary that is logged but
does not gate correctness, so the baseline is robust to LLM outages.

Runtime on vcpu=2 / 8gb: well under 60s per episode, ~3 minutes total,
comfortably inside the 20-minute hackathon ceiling.
"""
from __future__ import annotations

import asyncio
import os
import sys
import textwrap
from typing import Any, Dict, List, Optional

from openai import OpenAI

from fundlens.client import FundLensClient

# ── Mandatory environment variables ─────────────────────────────────────
# Defaults are intentionally provided ONLY for API_BASE_URL and MODEL_NAME,
# never for HF_TOKEN, per the pre-submission checklist.
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")  # required, no default

# Optional: only used by FundLensClient.from_docker_image()
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "fundlens:latest")

BENCHMARK = "fundlens"
TASKS: List[str] = ["easy", "medium", "hard"]

# How many LLM tokens the per-episode strategy prompt may consume. Kept
# tight so the total runtime stays well under the 20-minute budget.
LLM_MAX_TOKENS = 120
LLM_TEMPERATURE = 0.1

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are reviewing a private-equity reporting submission before it is
    graded. Given the fund id, the 8-line NAV bridge, and (optionally) the
    fund's MOIC/IRR, reply with ONE short sentence confirming whether the
    bridge appears consistent (ending_nav = cashflow_adjusted_nav +
    income_reversal + write_up_down). No markdown. No JSON. One sentence.
    """
).strip()


# ── Structured stdout helpers (locked to the sample contract) ───────────


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str],
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Strip newlines so the line stays single-line per the spec.
    action_clean = action.replace("\n", " ").replace("\r", " ")
    print(
        f"[STEP] step={step} action={action_clean} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def format_action_str(tool: str, arguments: Dict[str, Any]) -> str:
    """One-line action summary for the [STEP] action= field."""
    parts: List[str] = []
    for k, v in arguments.items():
        if isinstance(v, (dict, list)):
            parts.append(f"{k}=<{type(v).__name__}>")
        elif isinstance(v, str):
            parts.append(f"{k}='{v}'")
        else:
            parts.append(f"{k}={v}")
    return f"{tool}({','.join(parts)})"


# ── LLM call (OpenAI client, optional, non-gating) ─────────────────────


def llm_sanity_check(
    llm: OpenAI,
    fund_id: str,
    bridge: Dict[str, float],
    metrics: Optional[Dict[str, float]],
) -> Optional[str]:
    """One-shot per-episode sanity check. Returns the model's reply or None
    on any failure. Never raises -- if the LLM is unreachable the rest of
    the baseline keeps running against the environment."""
    summary_bridge = {k: round(float(v), 2) for k, v in bridge.items()}
    summary_metrics = (
        {k: round(float(v), 4) for k, v in (metrics or {}).items()} if metrics else {}
    )
    user_prompt = (
        f"fund_id: {fund_id}\n"
        f"nav_bridge: {summary_bridge}\n"
        f"metrics: {summary_metrics}"
    )
    try:
        completion = llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text or None
    except Exception as exc:
        print(f"[DEBUG] LLM sanity check failed (non-fatal): {exc}", flush=True)
        return None


# ── One episode ─────────────────────────────────────────────────────────


async def run_episode(env: FundLensClient, llm: OpenAI, task_id: str) -> float:
    """Run one full episode against a task and return its final reward.

    Baseline tool sequence:
        1. reset(task_id)
        2. get_available_filters -> fund_ids
        3. get_nav_bridge(fund_id=first) -> 8-line bridge dict
        4. [medium/hard only] get_portfolio_summary(funds=[fund_id]) -> MOIC (+IRR for hard)
        5. [llm sanity check, logged but non-gating]
        6. submit_report(nav_bridge=..., metrics=...) -> grading dict with reward
    """
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        # Step 1 -- reset (NOT counted in the step stream since the sample
        # only logs env.step() calls, but we still track it so the error
        # path surfaces cleanly if the env is unreachable).
        await env.reset(task_id=task_id)

        # Step 1 -- discover which fund_ids are loaded.
        steps_taken = 1
        try:
            filters = await env.call_tool("get_available_filters")
            fund_ids = filters.get("fund_ids") or []
            error = None
        except Exception as exc:
            fund_ids = []
            error = str(exc)
        log_step(
            step=1,
            action="get_available_filters()",
            reward=0.0,
            done=False,
            error=error,
        )
        rewards.append(0.0)

        if not fund_ids:
            # Can't proceed without a fund id -- end cleanly with score 0.
            return 0.0

        primary_fund = fund_ids[0]

        # Step 2 -- fetch the 8-line NAV bridge.
        steps_taken = 2
        bridge: Dict[str, float] = {}
        try:
            bridge = await env.call_tool("get_nav_bridge", fund_id=primary_fund)
            error = None
        except Exception as exc:
            error = str(exc)
        log_step(
            step=2,
            action=format_action_str("get_nav_bridge", {"fund_id": primary_fund}),
            reward=0.0,
            done=False,
            error=error,
        )
        rewards.append(0.0)

        # Step 3 (medium / hard only) -- fetch MOIC + IRR.
        metrics: Optional[Dict[str, float]] = None
        if task_id in ("medium", "hard"):
            steps_taken = 3
            try:
                summary = await env.call_tool(
                    "get_portfolio_summary", funds=[primary_fund]
                )
                fund_row = (summary or {}).get(primary_fund) or {}
                metrics = {}
                if "moic" in fund_row:
                    metrics["moic"] = float(fund_row["moic"])
                if task_id == "hard" and "irr" in fund_row:
                    metrics["irr"] = float(fund_row["irr"])
                error = None
            except Exception as exc:
                error = str(exc)
            log_step(
                step=3,
                action=format_action_str(
                    "get_portfolio_summary", {"funds": [primary_fund]}
                ),
                reward=0.0,
                done=False,
                error=error,
            )
            rewards.append(0.0)

        # Non-gating LLM sanity check (uses OpenAI client per checklist).
        commentary = llm_sanity_check(llm, primary_fund, bridge, metrics)
        if commentary:
            print(f"[DEBUG] LLM commentary: {commentary[:160]}", flush=True)

        # Final step -- submit the report and read the grader's reward.
        steps_taken += 1
        submit_args: Dict[str, Any] = {"nav_bridge": bridge}
        if metrics:
            submit_args["metrics"] = metrics
        reward = 0.0
        done = True
        error = None
        try:
            grading = await env.call_tool("submit_report", **submit_args)
            reward = float((grading or {}).get("reward") or 0.0)
        except Exception as exc:
            error = str(exc)
            reward = 0.0
        rewards.append(reward)
        log_step(
            step=steps_taken,
            action=format_action_str("submit_report", submit_args),
            reward=reward,
            done=done,
            error=error,
        )

        score = max(rewards)
        score = max(0.0, min(1.0, score))
        success = score > 0.5
    except Exception as exc:
        print(f"[DEBUG] Episode {task_id} crashed: {exc}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ── Entrypoint ──────────────────────────────────────────────────────────


async def main() -> None:
    if not HF_TOKEN:
        print(
            "[ERROR] HF_TOKEN is not set. Export HF_TOKEN=hf_... before running.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    llm = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    env: FundLensClient | None = None
    try:
        env = await FundLensClient.from_docker_image(LOCAL_IMAGE_NAME)
    except Exception as exc:
        print(
            f"[ERROR] Could not start env from Docker image '{LOCAL_IMAGE_NAME}': {exc}",
            file=sys.stderr,
            flush=True,
        )
        print(
            "[HINT] Build the image first: docker build -t fundlens:latest .",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(2)

    scores: Dict[str, float] = {}
    try:
        for task_id in TASKS:
            scores[task_id] = await run_episode(env, llm, task_id)
    finally:
        try:
            await env.close()
        except Exception as exc:
            print(f"[DEBUG] env.close() error: {exc}", flush=True)

    avg = sum(scores.values()) / len(scores) if scores else 0.0
    print(
        f"[SUMMARY] tasks={len(scores)} avg_score={avg:.2f} "
        f"per_task={','.join(f'{k}={v:.2f}' for k, v in scores.items())}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
