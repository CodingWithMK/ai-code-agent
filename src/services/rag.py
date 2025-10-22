import os
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.embeddings import resolve_embed_model

def load_documents(data_dir: str, llama_cloud_api_key: str | None):
    if llama_cloud_api_key:
        parser = LlamaParse(result_type="markdown")
        file_extractor = {".pdf": parser}
        print("[data] Using LlamaParse for PDF parsing.")
        return SimpleDirectoryReader(data_dir, file_extractor=file_extractor).load_data()
    else:
        print("[data] LLAMA_CLOUD_API_KEY not found. Using default reader fallback.")
        return SimpleDirectoryReader(data_dir).load_data()

def build_query_engine(llm, data_dir: str, llama_cloud_api_key: str | None):
    embed_model = resolve_embed_model("local:BAAI/bge-m3")
    docs = load_documents(data_dir, llama_cloud_api_key)
    index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)
    return index.as_query_engine(llm=llm)
