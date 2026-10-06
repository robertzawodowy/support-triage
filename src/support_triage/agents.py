"""The two agents. Model is resolved lazily so imports work without API keys."""
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from .config import MODEL
from .db import SupportDB
from .models import Reply, Triage


# --- Step 1: classifier (structured output, no tools) -----------------------
triage_agent = Agent(
    MODEL,
    output_type=Triage,
    instructions=(
        "You triage customer support tickets. Classify the category, rate urgency "
        "from 1 to 5 (5 = money lost or service down), judge sentiment, and extract "
        "an order id like 'A-1001' if present."
    ),
    defer_model_check=True,
)


# --- Step 2: responder (tools + dependency injection) ------------------------
@dataclass
class SupportDeps:
    db: SupportDB
    customer_id: str


support_agent = Agent(
    MODEL,
    deps_type=SupportDeps,
    output_type=Reply,
    instructions=(
        "You are a friendly support agent. Use the tools to look up facts; never "
        "invent order details. Set needs_human=True for angry customers, refunds "
        "over 100 EUR, or anything you cannot resolve from the tools."
    ),
    defer_model_check=True,
)


@support_agent.tool
def lookup_order(ctx: RunContext[SupportDeps], order_id: str) -> str:
    """Look up an order's status by id."""
    order = ctx.deps.db.get_order(order_id, ctx.deps.customer_id)
    return str(order) if order else "No such order for this customer."


@support_agent.tool
def search_faq(ctx: RunContext[SupportDeps], query: str) -> list[str]:
    """Search the FAQ for policy information."""
    return ctx.deps.db.search_faq(query) or ["No FAQ entry found."]
