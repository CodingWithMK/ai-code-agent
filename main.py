"""
CLI runner for the modular AI Code Agent

Uses:
- src/agents/ai_code_agent.AICodeAgent
- src/config for environment-driven settings

Run:
    uv run python main.py
"""

import os
import sys
import argparse

# Ensure project root is on sys.path (so `src.*` imports work when run from root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import (
    OLLAMA_BASE_URL, OLLAMA_TIMEOUT, OLLAMA_KEEP_ALIVE,
    OLLAMA_CHAT_MODEL, OLLAMA_CODE_MODEL, DATA_DIR, LLAMA_CLOUD_API_KEY
)
from src.agents.ai_code_agent import AICodeAgent


def ensure_dirs() -> None:
    """Create required local folders if not present."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)


def build_agent() -> AICodeAgent:
    """Construct and return the AICodeAgent with current env/config."""
    return AICodeAgent(
        base_url=OLLAMA_BASE_URL,
        timeout=OLLAMA_TIMEOUT,
        keep_alive=OLLAMA_KEEP_ALIVE,
        chat_model=OLLAMA_CHAT_MODEL,
        code_model=OLLAMA_CODE_MODEL,
        data_dir=DATA_DIR,
        llama_cloud_api_key=LLAMA_CLOUD_API_KEY,
    )


def run_interactive(agent: AICodeAgent) -> None:
    """Interactive REPL loop. Choose Plain (text) or Structured (code file) mode per prompt."""
    print("\n🧠 AI Code Agent — CLI")
    print("Type 'q' to quit.\n")

    while True:
        prompt = input("Enter a prompt (Press q to quit): ").strip()
        if prompt.lower() == "q":
            print("Bye!")
            break
        if not prompt:
            continue

        mode = input("Mode: [p]lain text / [s]tructured file output ? [p/s]: ").strip().lower() or "p"

        try:
            if mode == "s":
                result = agent.generate_structured(prompt)
                print("\n✅ Code generated")
                print("\nDescription:\n", result.description)
                print("\nCode:\n")
                print(result.code)

                # Save file
                out_path = os.path.join("output", result.filename)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(result.code)
                print(f"\n💾 Saved file: output/{result.filename}\n")

            else:
                text = agent.query_text(prompt)
                print("\n--- Agent Response (raw text) ---\n")
                print(text, "\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main() -> None:
    """Parse arguments and run in chosen mode."""
    parser = argparse.ArgumentParser(description="AI Code Agent (modular) — CLI runner")
    parser.add_argument(
        "--mode",
        choices=["plain", "structured", "repl"],
        default="repl",
        help="plain: single-shot text; structured: single-shot code file; repl: interactive loop",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="",
        help="Prompt to run in single-shot modes (plain/structured). Ignored in repl mode.",
    )
    args = parser.parse_args()

    ensure_dirs()
    agent = build_agent()

    # Single-shot modes
    if args.mode in {"plain", "structured"}:
        if not args.prompt:
            print("Please provide --prompt for single-shot mode.")
            sys.exit(2)

        try:
            if args.mode == "plain":
                text = agent.query_text(args.prompt)
                print("\n--- Agent Response (raw text) ---\n")
                print(text)

            else:
                result = agent.generate_structured(args.prompt)
                print("\n✅ Code generated")
                print("\nDescription:\n", result.description)
                print("\nCode:\n")
                print(result.code)

                out_path = os.path.join("output", result.filename)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(result.code)
                print(f"\n💾 Saved file: output/{result.filename}")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
        return

    # Default: interactive REPL
    run_interactive(agent)


if __name__ == "__main__":
    main()
