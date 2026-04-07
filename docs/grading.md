# Grading

Tolerance-based scoring with partial credit. Reward is always in `[0.0, 1.0]`.

## Tolerances

| Item                       | Tolerance     | Example                          |
|----------------------------|---------------|----------------------------------|
| NAV bridge line items      | +/- $0.50M    | Correct: 100.00, accept: 99.50 - 100.50 |
| MOIC (multiple)            | +/- 0.02x     | Correct: 1.50, accept: 1.48 - 1.52 |
| IRR                        | +/- 1.0% absolute | Correct: 0.150, accept: 0.140 - 0.160 |

These tolerances are defined in `packages/backend/fundlens/server/grader.py`:

```python
TOL_AMOUNT   = 0.50   # +/- $0.50M for NAV bridge
TOL_MULTIPLE = 0.02   # +/- 0.02x for MOIC
TOL_IRR      = 0.01   # +/- 1% absolute for IRR
```

## Per-task scoring weights

Different difficulty levels grade different things, and weight bridge vs metrics differently.

| Task   | Bridge weight | Metrics weight | What's graded                   |
|--------|---------------|----------------|----------------------------------|
| easy   | 100%          | 0%             | NAV bridge only (8 line items)   |
| medium | 60%           | 40%            | Bridge + MOIC                    |
| hard   | 50%           | 50%            | Bridge + MOIC + IRR              |

## Score computation

### Easy

```
bridge_score = number of bridge line items within tolerance (out of 8)
reward       = bridge_score / 8
```

### Medium

```
bridge_score = items within tolerance (out of 8)
metrics_score = MOIC within tolerance (0 or 1, out of 1)

bridge_reward  = bridge_score / 8
metrics_reward = metrics_score / 1

reward = 0.60 * bridge_reward + 0.40 * metrics_reward
```

### Hard

```
bridge_score = items within tolerance (out of 8)
metrics_score = MOIC within tolerance + IRR within tolerance (out of 2)

bridge_reward  = bridge_score / 8
metrics_reward = metrics_score / 2

reward = 0.50 * bridge_reward + 0.50 * metrics_reward
```

## Why partial credit

The grader gives credit for each line item independently. An agent that gets 7 of 8 bridge items right scores `0.875` on the bridge component, not `0`. This rewards close-but-not-perfect solutions and produces score variance across agents -- which the hackathon judges look for.

## What submission looks like

Agents call the `submit_report` MCP tool with the computed bridge and (optionally) metrics:

### Easy

```json
{
  "tool_name": "submit_report",
  "arguments": {
    "nav_bridge": {
      "beginning_nav": 38.5,
      "contribution": 0.0,
      "disposition": 5.5,
      "income": 2.73,
      "cashflow_adjusted_nav": 35.73,
      "income_reversal": -2.73,
      "write_up_down": 9.30,
      "ending_nav": 42.30
    }
  }
}
```

### Medium

```json
{
  "tool_name": "submit_report",
  "arguments": {
    "nav_bridge": { /* 8 items */ },
    "metrics": { "moic": 1.92 }
  }
}
```

### Hard

```json
{
  "tool_name": "submit_report",
  "arguments": {
    "nav_bridge": { /* 8 items */ },
    "metrics": { "moic": 2.34, "irr": 0.385 }
  }
}
```

## Grading response

`submit_report` returns the grading result:

```json
{
  "reward": 0.875,
  "task_id": "medium",
  "bridge_reward": 0.875,
  "metrics_reward": 0.875,
  "bridge_score": "7/8",
  "metrics_score": "1/1",
  "bridge_details": {
    "beginning_nav": true,
    "contribution": true,
    "disposition": true,
    "income": false,
    "cashflow_adjusted_nav": true,
    "income_reversal": true,
    "write_up_down": true,
    "ending_nav": true
  },
  "metrics_details": {
    "moic": true
  },
  "correct_nav_bridge": { /* the answer */ },
  "correct_metrics": { /* the answer */ }
}
```

The episode ends after `submit_report` is called. The agent gets one shot per episode.

## Determinism

Graders are deterministic. The seed data is hardcoded, the calculations are pure functions, and the tolerances are fixed. Running the same submission twice produces the same reward.

This satisfies one of the hackathon's pass/fail gates: graders must not always return the same score (which would mean no differentiation), but they must be reproducible.
