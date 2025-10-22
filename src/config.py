import os
from dotenv import load_dotenv

# Load .env if present; in CI/Prod we typically rely on real env vars
load_dotenv()

def env(key: str, default: str | None = None) -> str | None:
    """Small helper to read environment variables with an optional default."""
    return os.getenv(key, default)

# Non-secret defaults (safe to keep in code)
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = float(env("OLLAMA_TIMEOUT", "360"))
OLLAMA_KEEP_ALIVE = env("OLLAMA_KEEP_ALIVE", "1h")
OLLAMA_CHAT_MODEL = env("OLLAMA_CHAT_MODEL", "mistral:7b-instruct")
OLLAMA_CODE_MODEL = env("OLLAMA_CODE_MODEL", "codellama:7b-instruct")
DATA_DIR = env("DATA_DIR", "./data")

# Secret
LLAMA_CLOUD_API_KEY = env("LLAMA_CLOUD_API_KEY")

def require(var_value: str | None, var_name: str) -> None:
    """
    Fail-fast helper for secrets that are truly required.
    Call only if the feature strictly needs the var (e.g., LlamaParse).
    """
    if not var_value:
        raise RuntimeError(
            f"Missing required environment variable: {var_name}. "
            f"Set it in your local .env (never commit secrets) or in CI secrets."
        )
