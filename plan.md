# FridgeEnv — Project Status

**Hackathon:** Scaler x Meta PyTorch Hackathon (Round 1)
**Deadline:** April 8, 2026 11:59 PM
**HF Space:** https://surajmandalcell-fridge-env.hf.space
**GitHub:** https://github.com/surajmandalcell/food_waste_rl

---

## Completion Status

### Pass/Fail Gate

| Requirement | Status |
|-------------|--------|
| HF Space deploys, /reset returns 200 | ✅ Live |
| `openenv validate` passes (6/6) | ✅ |
| Dockerfile builds and runs | ✅ |
| inference.py runs with GLM-5.1 | ✅ Running |
| 3+ tasks, graders in [0.0, 1.0] | ✅ |

### All Requirements

| Requirement | Status |
|-------------|--------|
| Typed Pydantic models | ✅ |
| step/reset/state endpoints | ✅ |
| /health, /metadata, /schema, /mcp | ✅ |
| openenv.yaml | ✅ |
| 3 tasks with difficulty progression | ✅ |
| Deterministic graders | ✅ |
| Rich reward signal | ✅ |
| inference.py uses OpenAI client | ✅ |
| Env vars configurable (.env) | ✅ |
| Docker + HF Spaces | ✅ |
| README with all sections | ✅ |
| 137 tests (109 backend + 28 frontend) | ✅ |
| Mermaid diagrams (docs/) | ✅ |
| Interactive demo (npm run demo) | ✅ |
| Warm filmic grain UI | ✅ |

### Baseline Scores (actual)

| Agent | Easy | Medium | Hard |
|-------|------|--------|------|
| Random | 0.72 | 0.66 | 0.63 |
| FIFO | 1.00 | 0.99 | 0.99 |
| LLM (GLM-5.1) | 0.97 | 0.87* | pending* |

*inference.py still running — GLM API is slow (~5 min/call)

---

## Key Commands

```bash
npm run install:all     # Install everything
npm run test            # 109 backend tests
npm run test:frontend   # 28 frontend tests
npm run test:all        # All tests
npm run lint            # Ruff
npm run typecheck       # Mypy
npm run build           # Frontend build
npm run demo            # Live demo (starts server, opens browser)
npm run preflight       # Lint + typecheck + all tests + build
npm run docker:build    # Build Docker image
npm run inference       # Run LLM baseline (needs .env)
```
