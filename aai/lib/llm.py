"""LLM client helpers – supports local MLX, Ollama, Anthropic, and OpenAI."""

import os
import subprocess
import time
from typing import Any
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import requests
from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    """Read an integer env var with a safe fallback."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _clean_env(name: str) -> str | None:
    """Read and normalize an env var, returning None when empty."""
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip().strip('"').strip("'")
    return value or None


def _required_api_key(name: str) -> str:
    """Return a validated API key string for provider auth."""
    value = _clean_env(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    # Catch common placeholder values before sending a request.
    lowered = value.lower()
    if "xxxx" in lowered or "your_" in lowered or "replace" in lowered:
        raise RuntimeError(
            f"{name} appears to be a placeholder value. Set a real API key in .env."
        )

    return value


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
    local_max_tokens = _int_env("LOCAL_MAX_OUTPUT_TOKENS", 2048)

    if resolved == "local":
        start_mlx_server()
        model_id = requests.get("http://localhost:8080/v1/models", timeout=5).json()["data"][0]["id"]
        return ChatOpenAI(
            model=model_id,
            base_url="http://localhost:8080/v1",
            api_key="local",
            temperature=0,
            max_tokens=local_max_tokens,
        )

    elif resolved == "local-ollama":
        model_name = os.getenv("MODEL_NAME", "qwen3-vl:8b")
        ollama_num_predict = _int_env("OLLAMA_NUM_PREDICT", local_max_tokens)
        return ChatOllama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0,
            num_predict=ollama_num_predict,
        )

    elif resolved == "claude":
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        return ChatAnthropic(
            model=model_name,
            api_key=_required_api_key("ANTHROPIC_API_KEY"),
            temperature=0,
            cache=None
        )

    else:  # 'openai' or any unrecognised value
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        return ChatOpenAI(
            model=model_name,
            api_key=_required_api_key("OPENAI_API_KEY"),
            temperature=0,
            cache=None
        )
