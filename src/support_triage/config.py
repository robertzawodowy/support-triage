"""Model configuration. Override with the TRIAGE_MODEL env var,
e.g. TRIAGE_MODEL=openai:gpt-5 or ollama:llama3.2"""
import os

MODEL = os.getenv("TRIAGE_MODEL", "anthropic:claude-sonnet-4-6")
