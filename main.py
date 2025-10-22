from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, PromptTemplate
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from prompts import context
from code_reader import code_reader
from dotenv import load_dotenv

# Loading all required credentials from the existing ".env" file in the root directory
load_dotenv()

# Defining the local LLM we will use to interact with
llm = Ollama(model="mistral", request_timeout=30.0)

# Data parser tool for grabbing information out of our data for our agent
parser = LlamaParse(result_type="markdown")

# Explaning the parser where to find and extract the data needed.
file_extractor = {".pdf": parser}
documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()

# Defining the embedded model for the vector index calculations and vector index operations
embed_model = resolve_embed_model("local:BAAI/bge-m3")
vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine = vector_index.as_query_engine(llm=llm)

# Tools for our code agent
tools = [
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="api_documentation",
            description="This gives docomentation about code for an API. Use this for reading docs for the API."
        ),
    ),
    code_reader,
]

# The local code LLM for code create when needed. 
code_llm = Ollama(model="codellama")
agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=False, context=context)

while (prompt := input("Enter a prompt (Press q to quit): ")) != "q":
    result = agent.query(prompt)
    print(result)
