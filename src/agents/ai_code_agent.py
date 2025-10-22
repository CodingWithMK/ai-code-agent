import os
from typing import Optional

from llama_index.llms.ollama import Ollama
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent

from src.services.ollama_utils import check_ollama_health, model_in_tags, warmup_ollama
from src.services.rag import build_query_engine
from src.services.structuring import (
    build_output_pipeline, extract_text, robust_parse_to_dict, fallback_extract_code, CodeOutput
)
from src.tools.code_reader import code_reader
from src.prompts import context

class AICodeAgent:
    """Wraps LLMs, RAG engine, tools, and JSON structuring in one interface."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        keep_alive: str,
        chat_model: str,
        code_model: str,
        data_dir: str,
        llama_cloud_api_key: Optional[str] = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.keep_alive = keep_alive
        self.chat_model = chat_model
        self.code_model = code_model
        self.data_dir = data_dir
        self.llama_cloud_api_key = llama_cloud_api_key

        if not check_ollama_health(self.base_url):
            raise RuntimeError(f"Ollama at {self.base_url} is not reachable.")

        # Helpful warnings
        for m in (self.chat_model, self.code_model):
            if not model_in_tags(self.base_url, m):
                print(f"[warn] Model '{m}' not in tags. Run 'ollama pull {m}'.")

        # Warmups (non-fatal)
        warmup_ollama(self.base_url, self.chat_model, keep_alive)
        warmup_ollama(self.base_url, self.code_model, keep_alive)

        # Build LLMs (no temperature)
        self.chat_llm = Ollama(model=self.chat_model, base_url=self.base_url, request_timeout=self.timeout)
        self.code_llm = Ollama(model=self.code_model, base_url=self.base_url, request_timeout=self.timeout)

        # RAG over code model for better code faithfulness
        rag_engine = build_query_engine(self.code_llm, self.data_dir, self.llama_cloud_api_key)

        # Tools
        self.tools = [
            QueryEngineTool(
                query_engine=rag_engine,
                metadata=ToolMetadata(
                    name="api_documentation",
                    description="Reads and retrieves information from parsed API documentation."
                ),
            ),
            code_reader,
        ]

        # Agent (concise)
        concise_context = (
            "You are a coding assistant.\n"
            "- When you read a file, return its exact code inside a single fenced code block.\n"
            "- If the user asks for code, output only one clean runnable code block.\n"
            "- Return ONLY what is asked. Avoid summaries unless explicitly requested.\n"
            "- Use tools only when necessary.\n"
            "- Do not show your reasoning steps.\n"
        )
        self.agent = ReActAgent.from_tools(
            self.tools, llm=self.code_llm, verbose=True, max_iterations=5, context=concise_context
        )

        # Structuring pipeline (Pydantic JSON → CodeOutput)
        self.pipeline = build_output_pipeline(self.code_llm)

        os.makedirs("output", exist_ok=True)

    def query_text(self, prompt: str) -> str:
        """Plain agent query → returns text (no structuring)."""
        res = self.agent.query(prompt)
        return extract_text(res)

    def generate_structured(self, prompt: str) -> CodeOutput:
        """
        Orchestrates: agent.query → structure to {code, description, filename}.
        Has a fallback that extracts fenced code if JSON fails.
        """
        # Gentle nudge for echo tasks
        if "read" in prompt.lower() and ("content" in prompt.lower() or "contents" in prompt.lower() or "exact" in prompt.lower()):
            prompt += "\n\nReturn the code exactly as it is inside a single Python code block."

        agent_text = extract_text(self.agent.query(prompt))

        # JSON structuring
        next_result = self.pipeline.run(response=agent_text)
        structured_text = extract_text(next_result)

        try:
            payload = robust_parse_to_dict(structured_text)
            for k in ("code", "description", "filename"):
                if k not in payload:
                    raise KeyError(k)
        except Exception:
            # Fallback: extract from fenced code
            code_blk = fallback_extract_code(agent_text)
            if not code_blk:
                raise RuntimeError("Failed to parse structured output and no fenced code found.")
            payload = {
                "code": code_blk,
                "description": "Recovered from fenced code block (fallback).",
                "filename": "generated_code.py",
            }

        return CodeOutput(**payload)
