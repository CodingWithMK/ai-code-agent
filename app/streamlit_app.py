import os
import io
import streamlit as st

from src.config import (
    OLLAMA_BASE_URL, OLLAMA_TIMEOUT, OLLAMA_KEEP_ALIVE,
    OLLAMA_CHAT_MODEL, OLLAMA_CODE_MODEL, DATA_DIR, LLAMA_CLOUD_API_KEY
)
from src.agents.ai_code_agent import AICodeAgent

import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work
ROOT = Path(__file__).resolve().parents[1]  # .../ai-code-agent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="AI Code Agent", layout="wide")

# -------------- Helpers --------------
def ensure_dirs():
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

@st.cache_resource(show_spinner=True)
def build_agent_cached():
    return AICodeAgent(
        base_url=OLLAMA_BASE_URL,
        timeout=OLLAMA_TIMEOUT,
        keep_alive=OLLAMA_KEEP_ALIVE,
        chat_model=OLLAMA_CHAT_MODEL,
        code_model=OLLAMA_CODE_MODEL,
        data_dir=DATA_DIR,
        llama_cloud_api_key=LLAMA_CLOUD_API_KEY,
    )

# -------------- Sidebar --------------
st.sidebar.title("AI Code Agent (Local)")
st.sidebar.caption("Ollama + LlamaIndex + LlamaParse")

with st.sidebar.expander("Environment / Models", expanded=True):
    st.write(f"**Base URL:** {OLLAMA_BASE_URL}")
    st.write(f"**Chat Model:** {OLLAMA_CHAT_MODEL}")
    st.write(f"**Code Model:** {OLLAMA_CODE_MODEL}")
    st.write(f"**DATA_DIR:** {DATA_DIR}")
    if LLAMA_CLOUD_API_KEY:
        st.success("LlamaParse: Enabled")
    else:
        st.warning("LlamaParse: Disabled (fallback reader)")

if st.sidebar.button("Rebuild Agent"):
    st.cache_resource.clear()
    st.rerun()

# -------------- Main Layout --------------
st.title("🧠 AI Code Agent — Local Dev Assistant")
st.write("Read docs & code, reason, and generate scripts locally — **no external API**.")

ensure_dirs()
agent = build_agent_cached()

# Upload area
st.subheader("📥 Upload Files to `/data`")
uploaded_files = st.file_uploader(
    "Upload PDFs or code files (they will be saved into the `data/` folder)", type=None, accept_multiple_files=True
)
if uploaded_files:
    for uf in uploaded_files:
        path = os.path.join("data", uf.name)
        with open(path, "wb") as f:
            f.write(uf.getbuffer())
    st.success(f"Saved {len(uploaded_files)} file(s) to `data/`. You may click 'Rebuild Agent' if you added new PDFs.")

st.divider()

# Prompt area
st.subheader("💬 Ask the Agent")
prompt = st.text_area("Enter your instruction", height=120, placeholder="Read the contents of test.py and write a python script that calls the post endpoint to make a new item.")

col1, col2 = st.columns([1,1])
with col1:
    run_plain = st.button("Run (Text Only)")
with col2:
    run_structured = st.button("Run (Generate Code File)")

# Results
if run_plain and prompt.strip():
    with st.spinner("Thinking..."):
        text = agent.query_text(prompt.strip())
    st.markdown("**Agent Response (raw text):**")
    st.code(text)

if run_structured and prompt.strip():
    with st.spinner("Generating structured code..."):
        result = agent.generate_structured(prompt.strip())
    st.success("✅ Code generated")
    st.markdown("**Description**")
    st.write(result.description)
    st.markdown("**Code**")
    st.code(result.code, language="python")

    # Save to /output
    out_path = os.path.join("output", result.filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result.code)
    st.info(f"Saved file: `output/{result.filename}`")

    # Download button
    st.download_button(
        label="⬇️ Download generated file",
        data=result.code.encode("utf-8"),
        file_name=result.filename,
        mime="text/x-python",
    )