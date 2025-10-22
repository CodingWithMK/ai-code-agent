import re
from typing import Optional
from pydantic import BaseModel
from dirtyjson import loads as dirtyjson_loads
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_pipeline import QueryPipeline
from llama_index.core.prompts import PromptTemplate

class CodeOutput(BaseModel):
    code: str
    description: str
    filename: str

def build_output_pipeline(llm) -> QueryPipeline:
    parser = PydanticOutputParser(CodeOutput)
    strict_prefix = (
        "You are a JSON-only formatter.\n"
        "Given a prior LLM response, you MUST output ONLY valid JSON that matches the following schema.\n"
        "Do not include markdown, backticks, or any extra text — JSON only.\n\n"
    )
    # code_parser_template import eden yer: src/prompts.py
    from src.prompts import code_parser_template  # absolute import (Streamlit için güvenli)
    json_prompt_str = strict_prefix + parser.format(code_parser_template)
    json_prompt_tmpl = PromptTemplate(json_prompt_str)
    return QueryPipeline(chain=[json_prompt_tmpl, llm])

def extract_text(result_obj) -> str:
    for attr in ("text", "message", "response", "content"):
        if hasattr(result_obj, attr) and getattr(result_obj, attr):
            val = getattr(result_obj, attr)
            if hasattr(val, "content") and isinstance(val.content, str):
                return val.content
            if isinstance(val, str):
                return val
    return str(result_obj)

def robust_parse_to_dict(text: str) -> dict:
    cleaned = text.replace("assistant:", "").strip()
    return dirtyjson_loads(cleaned)

def fallback_extract_code(agent_text: str) -> Optional[str]:
    m = re.search(r"```(?:python)?\s*(.*?)```", agent_text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else None
