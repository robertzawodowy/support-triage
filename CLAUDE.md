# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Uses `uv` (Python 3.12+).

```bash
uv sync                                   # install deps
uv run pytest                             # all tests (offline, no API key needed)
uv run pytest tests/test_pipeline.py::test_high_urgency_forces_human_review   # single test
uv run triage "Where is my order A-1001?" c1   # CLI: [ticket text] [customer_id]
TRIAGE_MODEL=test uv run triage           # run offline with pydantic-ai's dummy model
```

Live runs go through EPAM DIAL and need `DIAL_API_URL`, `DIAL_API_KEY`, `DIAL_DEPLOYMENT_NAME` (env or `.env`; see `.env.example`). The deployment must support tools: check `features.tools` via `curl -s "$DIAL_API_URL/openai/models" -H "Api-Key: $DIAL_API_KEY"`. No linter is configured.

## Architecture

A pydantic-ai tutorial project (src layout, package `support_triage`, entry point `main()` in `__init__.py`). Pipeline in `pipeline.py::handle_ticket`:

1. `triage_agent` (no tools, `output_type=Triage`) classifies the ticket.
2. The structured `Triage` is formatted into the prompt for `support_agent` (tools + `deps_type=SupportDeps`, `output_type=Reply`). Usage is shared via `usage=triage_run.usage`.
3. A deterministic guardrail in code overrides the LLM: `urgency >= 4` forces `needs_human=True` with reason "High urgency".

Key points spanning files:
- Both agents are module-level singletons in `agents.py`, built with `defer_model_check=True` so importing works without API keys. `config.py` builds the model at import time: DIAL is Azure-OpenAI-compatible, so it's an `OpenAIChatModel` over `AzureProvider`. If DIAL vars are missing it returns a placeholder that errors only when a run is attempted, so tests import fine without credentials. `TRIAGE_MODEL=test` selects the offline dummy model.
- Tools (`lookup_order`, `search_faq`) get the fake in-memory `SupportDB` (`db.py`) through `RunContext[SupportDeps]`. `get_order` enforces customer scoping so one customer can't see another's orders; keep that invariant.
- `models.py` holds the Pydantic contracts (`Triage`, `Reply`, `Ticket`, `Category`).

## Testing

Tests never hit a real model: they use `agent.override(model=TestModel(...))` or `FunctionModel` to script tool calls and structured outputs. `asyncio_mode = "auto"`, so async tests need no decorator. Follow this pattern for new tests.

The README's roadmap lists upcoming steps (pydantic-graph human-approval gate, pydantic-evals) that are not yet implemented.
