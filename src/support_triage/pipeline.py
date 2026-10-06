"""Step 3: orchestrate the agents. Triage first, then hand off to the responder."""
from .agents import SupportDeps, support_agent, triage_agent
from .db import SupportDB
from .models import Reply, Ticket, Triage


async def handle_ticket(ticket: Ticket, db: SupportDB | None = None) -> tuple[Triage, Reply]:
    db = db or SupportDB()

    triage_run = await triage_agent.run(ticket.text)
    triage = triage_run.output

    # Pass the structured triage to the responder as context, and share usage
    # tracking so total token spend is visible across both agents.
    prompt = (
        f"Ticket: {ticket.text}\n\n"
        f"Triage: category={triage.category}, urgency={triage.urgency}, "
        f"sentiment={triage.sentiment}, order_id={triage.order_id}"
    )
    reply_run = await support_agent.run(
        prompt,
        deps=SupportDeps(db=db, customer_id=ticket.customer_id),
        usage=triage_run.usage,
    )
    reply = reply_run.output

    # Deterministic guardrail: code, not the LLM, has the final say on escalation.
    if triage.urgency >= 4 and not reply.needs_human:
        reply = reply.model_copy(update={"needs_human": True, "reason": "High urgency"})

    return triage, reply
