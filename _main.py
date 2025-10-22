from config import (
    OLLAMA_BASE_URL, OLLAMA_TIMEOUT, OLLAMA_KEEP_ALIVE,
    OLLAMA_CHAT_MODEL, OLLAMA_CODE_MODEL, DATA_DIR
)

import os
import time
from typing import Optional
import httpx

from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from prompts import context
from code_reader import code_reader


# --------------------------------------
# 1) Small Ollama helpers (health, warm)
# --------------------------------------
def check_ollama_health(base_url: str) -> bool:
    """Check if Ollama server is running and reachable."""
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=10.0)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[health] Ollama health check failed: {e}")
        return False


def model_in_tags(base_url: str, model: str) -> bool:
    """Verify if the model exists locally in Ollama's tag list."""
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=10.0)
        r.raise_for_status()
        tags = r.json().get("models", [])
        names = {m.get("name") for m in tags if "name" in m}
        return model in names
    except Exception as e:
        print(f"[tags] Could not fetch tags: {e}")
        return False


def warmup_ollama(base_url: str, model: str, keep_alive: str,
                  timeout: float = 180.0, retries: int = 3, backoff_sec: float = 5.0):
    """
    Warm up a model by generating a trivial response so it stays in memory.
    Includes retry + exponential backoff to survive cold starts.
    """
    payload = {
        "model": model,
        "prompt": "ping",
        "stream": False,
        "keep_alive": keep_alive,
    }

    for attempt in range(1, retries + 1):
        try:
            resp = httpx.post(f"{base_url}/api/generate", json=payload, timeout=timeout)
            resp.raise_for_status()
            print(f"[warmup] {model} warmed successfully.")
            return
        except Exception as e:
            print(f"[warmup] Warning: {model} warm-up attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                sleep_for = backoff_sec * (2 ** (attempt - 1))
                time.sleep(sleep_for)
    print(f"[warmup] Giving up warming {model}. Proceeding anyway.")


# ---------------------------------------------
# 2) Initialize LLMs with concise configuration
# ---------------------------------------------
def build_ollama_llm(model: str) -> Ollama:
    """
    Build an Ollama LLM configured for concise, deterministic outputs.
    """
    return Ollama(
        model=model,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_TIMEOUT,
        temperature=0.1,
        top_p=0.9,
        additional_kwargs={
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "num_predict": 512,
        },
    )


# ------------------------------
# 3) Data loading & index build
# ------------------------------
def load_documents(data_dir: str):
    """Load documents and optionally parse PDFs with LlamaParse."""
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if llama_key:
        parser = LlamaParse(result_type="markdown")
        file_extractor = {".pdf": parser}
        print("[data] Using LlamaParse for PDF parsing.")
        return SimpleDirectoryReader(data_dir, file_extractor=file_extractor).load_data()
    else:
        print("[data] LLAMA_CLOUD_API_KEY not found. Using default reader fallback.")
        return SimpleDirectoryReader(data_dir).load_data()


def build_query_engine(llm: Ollama):
    """Create a query engine using a local embedding model and VectorStoreIndex."""
    embed_model = resolve_embed_model("local:BAAI/bge-m3")
    documents = load_documents(DATA_DIR)
    vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    return vector_index.as_query_engine(llm=llm)


# ----------------------------
# 4) Tools & Agent definition
# ----------------------------
def build_tools(query_engine):
    """
    Build the toolset for the ReAct agent.
    Includes:
    - api_documentation: reads & searches the parsed API docs
    - code_reader: reads local code files from ./data directory
    """
    return [
        QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="api_documentation",
                description="Reads and retrieves information from parsed API documentation."
            ),
        ),
        code_reader,  # integrated new tool
    ]


def build_agent(tools, code_llm: Ollama):
    """
    Create a concise ReAct agent that uses the code model for reasoning.
    Limited steps to prevent overthinking.
    """
    concise_context = (
    "You are a coding assistant.\n"
    "- Be concise and to the point.\n"
    "- If you read the content of a file, return the code exactly as it is, inside a single fenced code block.\n"
    "- If the user asks for code, output only one clean runnable code block.\n"
    "- Do not explain or summarize unless explicitly asked.\n"
    "- Use tools only when necessary.\n"
    "- Do not show your reasoning steps.\n"
)


    return ReActAgent.from_tools(
        tools,
        llm=code_llm,
        verbose=True,
        max_iterations=5,
        context=concise_context,
    )


# -------------
# 5) Main loop
# -------------
def main():
    """
    Entry point of the agent:
    - Verify Ollama health and model availability
    - Warm up models (optional)
    - Build LLMs, RAG engine, tools, and agent
    - Run user prompt loop
    """
    if not check_ollama_health(OLLAMA_BASE_URL):
        print(f"[fatal] Ollama at {OLLAMA_BASE_URL} is not reachable. Make sure it's running.")
        return

    for m in (OLLAMA_CHAT_MODEL, OLLAMA_CODE_MODEL):
        if not model_in_tags(OLLAMA_BASE_URL, m):
            print(f"[warn] Model '{m}' not found in Ollama tags. Run 'ollama pull {m}'.")

    warmup_ollama(OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_KEEP_ALIVE)
    warmup_ollama(OLLAMA_BASE_URL, OLLAMA_CODE_MODEL, OLLAMA_KEEP_ALIVE)

    chat_llm = build_ollama_llm(OLLAMA_CHAT_MODEL)
    code_llm = build_ollama_llm(OLLAMA_CODE_MODEL)

    query_engine = build_query_engine(chat_llm)
    tools = build_tools(query_engine)
    agent = build_agent(tools, code_llm)

    while (prompt := input("Enter a prompt (Press q to quit): ")) != "q":
        result = agent.query(prompt)
        print(result)


if __name__ == "__main__":
    main()
