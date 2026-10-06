"""Tests run fully offline using pydantic-ai's TestModel / FunctionModel."""
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel
from pydantic_ai import ModelMessage, ModelResponse, ToolCallPart, TextPart

from support_triage.agents import SupportDeps, support_agent, triage_agent
from support_triage.db import SupportDB
from support_triage.models import Category, Ticket
from support_triage.pipeline import handle_ticket



def test_db_does_not_leak_other_customers_orders():
    db = SupportDB()
    assert db.get_order("A-1001", "c1") is not None
    assert db.get_order("A-1001", "c2") is None


async def test_triage_returns_structured_output():
    with triage_agent.override(model=TestModel(custom_output_args={
        "category": "shipping", "urgency": 2, "sentiment": "neutral",
        "summary": "Order late", "order_id": "A-1001"})):
        result = await triage_agent.run("Where is A-1001?")
    assert result.output.category == Category.SHIPPING
    assert result.output.order_id == "A-1001"


async def test_support_agent_calls_lookup_tool():
    def script(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        # First turn: call the tool. Second turn: return the final structured reply.
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("lookup_order", {"order_id": "A-1001"})])
        return ModelResponse(parts=[ToolCallPart(
            info.output_tools[0].name,
            {"body": "Your order is shipped.", "needs_human": False})])

    deps = SupportDeps(db=SupportDB(), customer_id="c1")
    with support_agent.override(model=FunctionModel(script)):
        result = await support_agent.run("Where is A-1001?", deps=deps)
    assert result.output.body == "Your order is shipped."


async def test_high_urgency_forces_human_review():
    triage_model = TestModel(custom_output_args={
        "category": "billing", "urgency": 5, "sentiment": "angry",
        "summary": "Double charged", "order_id": None})
    support_model = TestModel(call_tools=[], custom_output_args={
        "body": "Sorry!", "needs_human": False})
    with triage_agent.override(model=triage_model), support_agent.override(model=support_model):
        _, reply = await handle_ticket(Ticket(customer_id="c1", text="You charged me twice!!"))
    assert reply.needs_human is True
    assert reply.reason == "High urgency"
