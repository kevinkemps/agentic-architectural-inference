"""LLM client helpers – supports local MLX, Ollama, Anthropic, and OpenAI."""

import os
import subprocess
import time
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import requests
import tiktoken
from dotenv import load_dotenv

load_dotenv()


def _resolve_model_name(llm: Any) -> str | None:
    for attr in ("model_name", "model"):
        value = getattr(llm, attr, None)
        if isinstance(value, str) and value:
            return value
    return None


def estimate_prompt_tokens(llm: Any, system_prompt: str, human_content: str) -> int:
    """Estimate token usage for a system + human prompt pair."""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_content),
    ]

    if hasattr(llm, "get_num_tokens_from_messages"):
        try:
            return int(llm.get_num_tokens_from_messages(messages))
        except Exception:
            pass

    joined_content = "\n\n".join(part for part in (system_prompt, human_content) if part)

    if hasattr(llm, "get_num_tokens"):
        try:
            return int(llm.get_num_tokens(joined_content))
        except Exception:
            pass

    model_name = _resolve_model_name(llm)
    try:
        encoding = tiktoken.encoding_for_model(model_name) if model_name else tiktoken.get_encoding("cl100k_base")
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(joined_content))


# ---------------------------------------------------------------------------
# Multi-provider model factory
# ---------------------------------------------------------------------------

def start_mlx_server(model_id: str = "mlx-community/Qwen2.5-7B-Instruct-4bit", port: int = 8080) -> Any:
    """Start an MLX LM server if one is not already running.

    Returns the subprocess.Popen handle, or None if the server was already up.
    """
    try:
        requests.get(f"http://localhost:{port}/v1/models", timeout=2)
        print(f"Server already running on port {port}.")
        return None
    except Exception:
        print(f"Starting MLX server with {model_id}...")
        cmd = ["python", "-m", "mlx_lm.server", "--model", model_id, "--port", str(port)]
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(30):
            try:
                requests.get(f"http://localhost:{port}/v1/models", timeout=1)
                print("Server is ready!")
                return process
            except Exception:
                time.sleep(2)
        print("Failed to start server.")
        return None


def get_model(provider: str | None = None):
    """Return a LangChain chat model based on the LLM_PROVIDER env var (or explicit arg).

    Supported providers (set LLM_PROVIDER in .env or pass ``provider`` directly):
      - ``'local'``        : MLX local server via ChatOpenAI-compatible wrapper
      - ``'local-ollama'`` : Ollama via ChatOllama
      - ``'claude'``       : Anthropic Claude via ChatAnthropic
      - ``'openai'``       : OpenAI GPT-4o via ChatOpenAI (default)
    """

    resolved = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

    if resolved == "local":
        start_mlx_server()
        model_id = requests.get("http://localhost:8080/v1/models", timeout=5).json()["data"][0]["id"]
        return ChatOpenAI(
            model=model_id,
            base_url="http://localhost:8080/v1",
            api_key="local",
            temperature=0,
        )

    elif resolved == "local-ollama":
        model_name = os.getenv("MODEL_NAME", "qwen3-vl:8b")
        return ChatOllama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0,
        )

    elif resolved == "claude":
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        return ChatAnthropic(
            model=model_name,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0,
        )

    else:  # 'openai' or any unrecognised value
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        return ChatOpenAI(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )
