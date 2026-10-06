"""Pydantic models: the structured contracts between agents."""
from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    BILLING = "billing"
    SHIPPING = "shipping"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    OTHER = "other"


class Triage(BaseModel):
    """Step 1 output: how the ticket is classified."""

    category: Category
    urgency: int = Field(ge=1, le=5, description="1 = low, 5 = critical")
    sentiment: str = Field(description="angry, neutral or happy")
    summary: str = Field(description="One-sentence summary of the problem")
    order_id: str | None = Field(default=None, description="Order id if mentioned")


class Reply(BaseModel):
    """Step 2 output: the drafted answer."""

    body: str
    needs_human: bool = Field(description="True if a person should review before sending")
    reason: str | None = Field(default=None, description="Why a human is needed")


class Ticket(BaseModel):
    customer_id: str
    text: str
