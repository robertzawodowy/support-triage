import asyncio
import sys

from .models import Ticket
from .pipeline import handle_ticket


def main() -> None:
    """Usage: uv run triage "My order A-1001 hasn't arrived" [customer_id]"""
    text = sys.argv[1] if len(sys.argv) > 1 else "Where is my order A-1001?"
    customer = sys.argv[2] if len(sys.argv) > 2 else "c1"
    triage, reply = asyncio.run(handle_ticket(Ticket(customer_id=customer, text=text)))
    print(triage.model_dump_json(indent=2))
    print("\n--- Reply ---")
    print(reply.body)
    print(f"\nHuman review needed: {reply.needs_human}" + (f" ({reply.reason})" if reply.reason else ""))
