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

## How it works

`pipeline.py::handle_ticket` runs the flow for one `Ticket(customer_id, text)`:

1. **Triage.** `triage_agent` has no tools and returns a `Triage`: `category`
   (billing, shipping, technical, account, other), `urgency` (1-5), `sentiment`,
   a one-sentence `summary`, and an `order_id` if the ticket mentions one.
2. **Respond.** The `Triage` is added to the prompt for `support_agent`, which
   returns a `Reply` (`body`, `needs_human`, `reason`). It has two tools, both
   reading from an injected `SupportDB` (`SupportDeps`):
   - `lookup_order(order_id)`: order status and ETA. Scoped to the ticket's
     `customer_id`, so another customer's order is reported as not found.
   - `search_faq(query)`: policy text (refund, password, shipping) by keyword.
3. **Guardrail.** After the LLM answers, code checks `triage.urgency >= 4` and
   forces `needs_human=True` with reason "High urgency" if the model didn't
   already escalate. The model may also escalate on its own (angry customer,
   refund over 100 EUR, anything the tools can't resolve), but it can never
   *skip* escalation for high urgency.

Token usage is shared across both agents through one `usage` object.

Example (`uv run triage "Where is my order A-1001?" c1`):

```
{"category": "shipping", "urgency": 3, "sentiment": "neutral", "order_id": "A-1001", ...}

--- Reply ---
Your order A-1001 has shipped and should arrive by October 9, 2026.

Human review needed: False
```

### Model configuration

`config.py` picks the model when the package is imported. Live runs go through
EPAM DIAL (an Azure-OpenAI-compatible gateway) using `DIAL_API_URL`,
`DIAL_API_KEY` and `DIAL_DEPLOYMENT_NAME`, read from the environment or `.env`.
The deployment must support tool calling. With `TRIAGE_MODEL=test` the agents
use pydantic-ai's offline dummy model, and if the DIAL variables are missing a
run fails with a message naming them (imports and tests still work).

## Tutorial steps and where to look

| Step | Concept | File |
|------|---------|------|
| 1 | Agent with structured `output_type` | `models.py`, `agents.py` (`triage_agent`) |
| 2 | Tools + dependency injection (`deps_type`, `RunContext`) | `agents.py` (`support_agent`), `db.py` |
| 3 | Multi-agent handoff, shared usage, deterministic guardrail | `pipeline.py` |
| 4 | Testing with `TestModel` / `FunctionModel` / `override` | `tests/` |
| 5 (next) | Graph with human approval gate (`pydantic-graph`) | to do |
| 6 (next) | Evals with `pydantic-evals` | to do |
