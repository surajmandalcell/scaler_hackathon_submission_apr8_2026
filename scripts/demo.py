#!/usr/bin/env python3
"""
FridgeEnv Live Demo
===================
Starts the actual server, hits real HTTP endpoints, opens the browser,
and walks through the full environment lifecycle with visible pacing.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time

import httpx

# ── Config ───────────────────────────────────────────────────────────

SERVER_PORT = 7860
SERVER_URL = f"http://localhost:{SERVER_PORT}"
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "packages", "backend")

# ── Terminal colors ──────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RS = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
WHITE = "\033[97m"


def color_score(score: float) -> str:
    pct = f"{score * 100:.0f}%"
    if score >= 0.8:
        return f"{GREEN}{BOLD}{pct}{RS}"
    if score >= 0.5:
        return f"{YELLOW}{pct}{RS}"
    return f"{RED}{pct}{RS}"


def banner(text: str) -> None:
    w = 62
    print(f"\n{CYAN}{'━' * w}{RS}")
    print(f"{CYAN}  {BOLD}{text}{RS}")
    print(f"{CYAN}{'━' * w}{RS}\n")


def section(text: str) -> None:
    print(f"\n{MAGENTA}{BOLD}▸ {text}{RS}")
    print(f"{MAGENTA}{'─' * 58}{RS}")


def step_pause(msg: str = "") -> None:
    """Small delay so output feels like a real process, not a dump."""
    if msg:
        print(f"  {DIM}{msg}{RS}", end="", flush=True)
    time.sleep(0.4)
    if msg:
        print()


def wait_for_server(url: str, timeout: int = 15) -> bool:
    """Poll until server responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                return True
        except httpx.ConnectError:
            pass
        time.sleep(0.5)
    return False


# ── Server management ────────────────────────────────────────────────

def start_server() -> subprocess.Popen:
    """Start uvicorn in background, return process handle."""
    proc = subprocess.Popen(
        ["uv", "run", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(SERVER_PORT)],
        cwd=os.path.abspath(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


# ── HTTP helpers ─────────────────────────────────────────────────────

def api_reset(client: httpx.Client, task_id: str, seed: int) -> dict:
    r = client.post(f"{SERVER_URL}/reset", json={"task_id": task_id, "seed": seed})
    r.raise_for_status()
    return r.json()


def api_step(client: httpx.Client, action: dict) -> dict:
    r = client.post(f"{SERVER_URL}/step", json=action)
    r.raise_for_status()
    return r.json()


def api_state(client: httpx.Client) -> dict:
    r = client.get(f"{SERVER_URL}/state")
    r.raise_for_status()
    return r.json()


def build_fifo_plan(obs: dict) -> dict:
    """Simple FIFO agent logic over HTTP observation dict."""
    inv = sorted(obs["inventory"], key=lambda x: x["expiry_date"])
    available = {i["name"]: i["quantity"] for i in inv}
    plan = []
    for day in range(1, obs["horizon"] + 1):
        ingredients = []
        used = set()
        for item in inv:
            n = item["name"]
            if n in used or available.get(n, 0) <= 0:
                continue
            # Urgent items: use everything. Others: spread across remaining days.
            days_left_str = item["expiry_date"]
            from datetime import date as dt_date
            exp = dt_date.fromisoformat(days_left_str)
            cur = dt_date.fromisoformat(obs["current_date"])
            urgency = (exp - cur).days - day
            if urgency <= 1:
                portion = available[n]
            else:
                portion = available[n] / max(1, obs["horizon"] - day + 1)
                portion = max(portion, available[n] * 0.3)
                portion = min(portion, available[n])
            if portion > 0:
                ingredients.append({"name": n, "quantity": round(portion, 1)})
                available[n] -= portion
                used.add(n)
            if len(ingredients) >= 5:
                break
        if ingredients:
            plan.append({"day": day, "meal_name": f"day{day}", "ingredients": ingredients})
    return {"meal_plan": plan}


# ── Main Demo ────────────────────────────────────────────────────────

def main() -> None:
    banner("FridgeEnv — Live Demo")
    server_proc = None

    try:
        # ── Start server ─────────────────────────────────────────
        section("Starting Server")
        print(f"  Launching uvicorn on port {SERVER_PORT}...")
        server_proc = start_server()
        time.sleep(0.5)

        if not wait_for_server(SERVER_URL):
            print(f"  {RED}Server failed to start!{RS}")
            if server_proc:
                out, err = server_proc.communicate(timeout=5)
                print(f"  stderr: {err.decode()[-500:]}")
            sys.exit(1)

        print(f"  {GREEN}Server is live at {SERVER_URL}{RS}")

        # Open browser
        try:
            import webbrowser
            webbrowser.open(SERVER_URL)
            print(f"  {DIM}Opened browser → {SERVER_URL}{RS}")
        except Exception:
            print(f"  {DIM}Open {SERVER_URL} in your browser to see the UI{RS}")

        time.sleep(1)
        client = httpx.Client(timeout=10)

        # ── Health check ─────────────────────────────────────────
        section("Health Check")
        r = client.get(f"{SERVER_URL}/health")
        print(f"  GET /health → {r.status_code}  {r.json()}")
        step_pause()

        # ── Run through each difficulty ──────────────────────────
        for difficulty in ["easy", "medium", "hard"]:
            section(f"Episode: {difficulty.upper()}")

            # Reset
            step_pause("Resetting environment...")
            obs = api_reset(client, difficulty, seed=42)
            inv = obs["inventory"]
            print(f"  {WHITE}{BOLD}{len(inv)} items{RS} in fridge, "
                  f"horizon={obs['horizon']}d, household={obs['household_size']}p")
            if obs.get("dietary_restrictions"):
                print(f"  {YELLOW}Restrictions: {', '.join(obs['dietary_restrictions'])}{RS}")

            # Show inventory
            step_pause()
            sorted_inv = sorted(inv, key=lambda x: x["expiry_date"])
            for item in sorted_inv[:6]:
                from datetime import date as dt_date
                days = (dt_date.fromisoformat(item["expiry_date"])
                        - dt_date.fromisoformat(obs["current_date"])).days
                icon = f"{RED}⚠{RS}" if days <= 2 else " "
                print(f"  {icon} {item['name'].replace('_', ' '):22s} "
                      f"{item['quantity']:>7.0f}{item['unit']:3s}  "
                      f"{'expires in ' + str(days) + 'd':>16s}  "
                      f"{DIM}{item['category']}{RS}")
            if len(inv) > 6:
                print(f"  {DIM}  + {len(inv) - 6} more items{RS}")

            # Plan meals
            step_pause("FIFO agent planning meals...")
            plan = build_fifo_plan(obs)
            n_meals = len(plan["meal_plan"])
            n_ingredients = sum(len(m["ingredients"]) for m in plan["meal_plan"])
            print(f"  Planned {n_meals} meals using {n_ingredients} ingredient slots")

            # Show a couple meals
            for meal in plan["meal_plan"][:3]:
                items_str = ", ".join(
                    f"{i['name'].replace('_', ' ')} ({i['quantity']:.0f})"
                    for i in meal["ingredients"][:3]
                )
                extra = f" +{len(meal['ingredients']) - 3}" if len(meal["ingredients"]) > 3 else ""
                print(f"    Day {meal['day']}: {items_str}{extra}")
            if n_meals > 3:
                print(f"    {DIM}...{n_meals - 3} more days{RS}")

            # Submit
            step_pause("Submitting plan to environment...")
            result = api_step(client, plan)
            reward = result["reward"]
            info = result["info"]

            print(f"\n  {BOLD}┌─ Results ─────────────────────────────┐{RS}")
            print(f"  {BOLD}│{RS}  Grader Score:    {color_score(reward['score']):>25s}  {BOLD}│{RS}")
            print(f"  {BOLD}│{RS}  Waste Rate:      {reward['waste_rate'] * 100:>14.0f}%         {BOLD}│{RS}")
            print(f"  {BOLD}│{RS}  Nutrition:       {reward['nutrition_score'] * 100:>14.0f}%         {BOLD}│{RS}")
            print(f"  {BOLD}│{RS}  Items Used:      {reward['items_used']:>14d}          {BOLD}│{RS}")
            print(f"  {BOLD}│{RS}  Items Expired:   {reward['items_expired']:>14d}          {BOLD}│{RS}")
            violations = reward.get("violations", [])
            if violations:
                print(f"  {BOLD}│{RS}  Violations:      {RED}{len(violations):>14d}{RS}          {BOLD}│{RS}")
            print(f"  {BOLD}└───────────────────────────────────────┘{RS}")

            # Verify state
            state = api_state(client)
            assert state["done"] is True
            step_pause()

        # ── Agent comparison ─────────────────────────────────────
        section("Agent Comparison (50 episodes each via HTTP)")

        sys.path.insert(0, os.path.abspath(BACKEND_DIR))
        from agents.fifo_agent import FIFOAgent
        from agents.random_agent import RandomAgent

        header = f"  {'Agent':12s} {'Difficulty':10s} {'Avg Score':>10s} {'Avg Waste':>10s}"
        print(f"\n{BOLD}{header}{RS}")
        print(f"  {'─' * 44}")

        for AgentClass, name in [(RandomAgent, "Random"), (FIFOAgent, "FIFO")]:
            for diff in ["easy", "medium", "hard"]:
                scores = []
                wastes = []
                agent = AgentClass(seed=0) if name == "Random" else AgentClass()
                for seed in range(50):
                    obs = api_reset(client, diff, seed)
                    plan = agent.act(obs)
                    result = api_step(client, plan)
                    scores.append(result["reward"]["score"])
                    wastes.append(result["reward"]["waste_rate"])
                avg_s = sum(scores) / len(scores)
                avg_w = sum(wastes) / len(wastes)
                print(f"  {name:12s} {diff:10s} {color_score(avg_s):>19s} "
                      f"{avg_w * 100:>9.1f}%")

        # ── Determinism proof ────────────────────────────────────
        section("Determinism Proof")
        print()
        for diff in ["easy", "medium", "hard"]:
            s1 = api_reset(client, diff, 777)
            r1 = api_step(client, build_fifo_plan(s1))["reward"]["score"]
            s2 = api_reset(client, diff, 777)
            r2 = api_step(client, build_fifo_plan(s2))["reward"]["score"]
            ok = r1 == r2
            tag = f"{GREEN}MATCH{RS}" if ok else f"{RED}MISMATCH{RS}"
            print(f"  {diff:8s}  seed=777  run1={r1:.4f}  run2={r2:.4f}  [{tag}]")

        step_pause()

        # ── Done ─────────────────────────────────────────────────
        banner("Demo Complete — Server Still Running")
        print(f"  {WHITE}The server is live at {BOLD}{SERVER_URL}{RS}")
        print(f"  {WHITE}The frontend is open in your browser.{RS}")
        print(f"  {DIM}Try clicking Reset / Run FIFO Agent in the UI.{RS}")
        print(f"\n  {DIM}Press Ctrl+C to stop the server and exit.{RS}\n")

        # Keep server alive until Ctrl+C
        server_proc.wait()

    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Shutting down...{RS}")
    finally:
        if server_proc and server_proc.poll() is None:
            server_proc.terminate()
            server_proc.wait(timeout=5)
            print(f"  {DIM}Server stopped.{RS}\n")


if __name__ == "__main__":
    main()
