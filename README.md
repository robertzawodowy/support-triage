# Support Triage: an agentic workflow with pydantic-ai

A two-agent pipeline: **classify** a support ticket into structured data, then
**respond** using tools backed by an injected (fake) database, with a code-level
escalation guardrail.

```
Ticket -> triage_agent -> Triage (Pydantic) -> support_agent (+tools, +deps) -> Reply
                                                        |
                                    guardrail: urgency >= 4 => needs_human
```

## Run

```bash
uv sync
cp .env.example .env                    # then fill in DIAL_API_URL, DIAL_API_KEY, DIAL_DEPLOYMENT_NAME
# list deployments (pick one with features.tools == true):
curl -s "$DIAL_API_URL/openai/models" -H "Api-Key: $DIAL_API_KEY"
uv run triage "Where is my order A-1001?" c1
uv run triage "You charged me twice, this is unacceptable!" c1
TRIAGE_MODEL=test uv run triage         # offline, no key needed (dummy output)
uv run pytest                           # offline tests
```

## Tutorial steps and where to look

| Step | Concept | File |
|------|---------|------|
| 1 | Agent with structured `output_type` | `models.py`, `agents.py` (`triage_agent`) |
| 2 | Tools + dependency injection (`deps_type`, `RunContext`) | `agents.py` (`support_agent`), `db.py` |
| 3 | Multi-agent handoff, shared usage, deterministic guardrail | `pipeline.py` |
| 4 | Testing with `TestModel` / `FunctionModel` / `override` | `tests/` |
| 5 (next) | Graph with human approval gate (`pydantic-graph`) | to do |
| 6 (next) | Evals with `pydantic-evals` | to do |
