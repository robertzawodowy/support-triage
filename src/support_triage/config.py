"""Model configuration for EPAM DIAL (Azure-OpenAI-compatible gateway).

Required env vars (or a .env file):
  DIAL_API_URL          bare host, e.g. https://ai-proxy.lab.epam.com
  DIAL_API_KEY
  DIAL_DEPLOYMENT_NAME  list with: curl -s "$DIAL_API_URL/openai/models" -H "Api-Key: $DIAL_API_KEY"
                        (pick one with features.tools == true; the agents use tool calling)

TRIAGE_MODEL=test switches to pydantic-ai's offline dummy model.
"""
import os

from dotenv import load_dotenv
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

load_dotenv()  # must run before the getenv calls below

DIAL_API_VERSION = "2023-12-01-preview"


def _missing_config(missing: list[str]) -> Model:
    """Import-safe placeholder that fails with a clear message only when actually used."""

    def fail(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise RuntimeError(f"DIAL is not configured; set {', '.join(missing)} (see README).")

    return FunctionModel(fail)


def build_model() -> Model | str:
    if os.getenv("TRIAGE_MODEL") == "test":
        return "test"
    env = {k: os.getenv(k) for k in ("DIAL_API_URL", "DIAL_API_KEY", "DIAL_DEPLOYMENT_NAME")}
    if missing := [k for k, v in env.items() if not v]:
        return _missing_config(missing)
    provider = AzureProvider(
        azure_endpoint=env["DIAL_API_URL"],
        api_key=env["DIAL_API_KEY"],
        api_version=DIAL_API_VERSION,
    )
    return OpenAIChatModel(env["DIAL_DEPLOYMENT_NAME"], provider=provider)


MODEL = build_model()
