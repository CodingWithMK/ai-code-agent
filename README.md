# 🧠 AI Code Agent

### A Local, Generative AI (RAG) Code Agent

> An intelligent **code-reading and reasoning agent** built with **LlamaIndex**, **Ollama**, and **LlamaParse**.
> The agent runs **entirely offline**, analyzes local files, retrieves documentation, and generates new code — all without sending data to external APIs.

---

## 🚀 Overview

**AI Code Agent** is a local RAG-based (Retrieval-Augmented Generation) system that combines:

* **Ollama LLMs** (`mistral`, `codellama`, etc.) for reasoning and generation
* **LlamaIndex** for document parsing, embeddings, and tool orchestration
* **LlamaParse** for extracting structured text from PDF documentation
* **Custom tools** such as `code_reader` to inspect local files

It was built as part of the **Global AI Hub Generative AI Bootcamp** project, focusing on modular agent design and privacy-centric LLM workflows.

---

## 🧩 Core Features

| Feature                       | Description                                                                                               |
| ----------------------------- | --------------------------------------------------------------------------------------------------------- |
| 💬 **ReAct Agent**            | A reasoning-and-action architecture that dynamically decides when to read, think, or code.                |
| 🧠 **Local Ollama Models**    | Uses local LLMs (e.g., `mistral:7b-instruct`, `codellama:7b-instruct`) with no external API calls.        |
| 🧾 **PDF Knowledge Parsing**  | Automatically parses API documentation PDFs using **LlamaParse** and indexes them via **LlamaIndex**.     |
| 🗂️ **Vector Search (RAG)**   | Converts parsed text into vector embeddings (`BAAI/bge-m3`) for fast contextual retrieval.                |
| 🧰 **Code Reader Tool**       | Reads any file inside the `/data` folder and returns its exact content for code understanding or editing. |
| ⚙️ **Flexible Configuration** | Environment variables control all models and services via `.env` / `.env.example`.                        |
| 🔐 **Local & Private**        | Entirely offline — no data leaves your machine.                                                           |
| 🧩 **Extendable**             | Easily add new tools (e.g., code writer, file saver, web fetcher).                                        |

---

## 🏗️ Tech Stack

* **Language:** Python 3.10+
* **LLM Runtime:** [Ollama](https://ollama.ai)
* **Framework:** [LlamaIndex](https://docs.llamaindex.ai)
* **Parser:** [LlamaParse](https://www.llamaindex.ai/llamaparse)
* **Environment:** [uv package manager](https://docs.astral.sh/uv/)
* **Embeddings:** `BAAI/bge-m3` (local Hugging Face model)
* **Agent Architecture:** ReAct (Reason + Act loop)

---

## 📂 Project Structure

```
ai-code-agent/
│
├── _main.py              # Main entrypoint (agent orchestration)
├── code_reader.py        # Custom FunctionTool for reading local code files
├── prompts.py            # Agent purpose and behavior context
├── config.py             # Centralized environment configuration
├── requirements.txt      # Dependency list
├── .env.example          # Safe environment template
├── .gitignore            # Protects secrets (.env, cache, etc.)
└── /data/                # Local PDFs, source files, and docs to analyze
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/ai-code-agent.git
cd ai-code-agent
```

### 2️⃣ Create a virtual environment

Using **uv** (recommended):

```bash
uv sync
```

or traditional pip:

```bash
python -m venv venv
source venv/bin/activate     # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

### 3️⃣ Configure environment variables

Create your local `.env` from the template:

```bash
cp .env.example .env
```

Then open `.env` and fill in your local or secret keys:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=360
OLLAMA_KEEP_ALIVE=-1
OLLAMA_CHAT_MODEL=mistral:7b-instruct
OLLAMA_CODE_MODEL=codellama:7b-instruct
DATA_DIR=./data
LLAMA_CLOUD_API_KEY=your_llamaparse_api_key_here
```

### 4️⃣ Pull Ollama models

```bash
ollama pull mistral:7b-instruct
ollama pull codellama:7b-instruct
```

### 5️⃣ Run the Ollama service

```bash
ollama serve
```

### 6️⃣ Launch the agent

```bash
uv run python _main.py
```

---

## 🧪 Example Interaction

```
Enter a prompt (Press q to quit):
> Read the content of test.py and give me the exact same code back.
```

Agent internally:

1. Detects intent → uses the **code_reader** tool.
2. Reads `/data/test.py`.
3. Returns the exact code inside a Python code block.

Output:

```python
from flask import Flask, jsonify, request

app = Flask(__name__)
# ...
if __name__ == "__main__":
    app.run(debug=True)
```

---

## 🧰 Custom Tools

### 🧩 `code_reader.py`

```python
from llama_index.core.tools import FunctionTool
import os

def code_reader_func(file_name):
    path = os.path.join("data", file_name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            return {"code": content}
    except Exception as e:
        return {"error": str(e)}

code_reader = FunctionTool.from_defaults(
    fn=code_reader_func,
    name="code_reader",
    description="Reads and returns the exact content of a code file from the data directory."
)
```

> This tool allows the agent to “open” and analyze local code files dynamically.

---

## 🧠 Agent Architecture

The agent uses **LlamaIndex’s ReActAgent**, which follows a loop:

```
Thought → Action (tool) → Observation → Reasoning → Final Answer
```

* When a user asks about documentation → uses `api_documentation` (RAG engine).
* When a user asks to “read code” → invokes `code_reader`.
* When a user asks to “generate code” → directly uses the LLM (`codellama`).

Its reasoning steps are limited (`max_iterations=5`) to prevent “overthinking” and ensure fast responses.

---

## 🔒 Security & Privacy

* No external API calls from the LLM (Ollama runs locally).
* `.env` file is excluded from version control via `.gitignore`.
* `.env.example` serves as a public, non-secret template.
* You can safely share this repo without exposing API keys.

---

## 🧭 Environment Config Management

* All environment variables are loaded via `config.py`.
* Secure defaults ensure the app runs even without `.env`.
* Secrets such as `LLAMA_CLOUD_API_KEY` are never hardcoded.
* In CI/CD (e.g., GitHub Actions), store secrets under
  **Settings → Secrets → Actions**.

---

## 🧠 Future Enhancements

| Planned Feature                        | Description                                       |
| -------------------------------------- | ------------------------------------------------- |
| ✍️ **Code Writer Tool**                | Generate and save new Python files from prompts.  |
| 🧩 **File Saver / Editor**             | Automatically apply LLM-suggested modifications.  |
| 🔎 **Web Fetcher Tool**                | Retrieve and summarize online documentation.      |
| 🧱 **Memory Module**                   | Persistent long-term memory for multi-turn tasks. |
| 🪶 **Async Warm-Up with Progress Bar** | Show model-loading progress during startup.       |

---

## 🤝 Contributing

Contributions are welcome!
Please open a pull request or issue if you:

* Found a bug 🐞
* Have an idea for a new tool ⚒️
* Want to add support for another Ollama model 💡

Steps:

```bash
git checkout -b feature/my-new-tool
git commit -m "Add new feature"
git push origin feature/my-new-tool
```

---

## 📜 License

This project is released under the **MIT License**.
Feel free to modify, extend, and use it for your personal or educational projects.

---

## 🧩 Credits

Developed by **Musab Kaya** as part of the
**Global AI Hub – Generative AI Bootcamp 2025**.

---