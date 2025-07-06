from dotenv import load_dotenv
from agents.mcp import MCPServerStdio
import os

load_dotenv(override=True)

GRAPH_DB = "./memory/graph.db"
RAG_DB = "./memory/knowledge/"

memory_graph_params = {
    "command": "npx",
    "args": ["-y", "mcp-memory-libsql"],
    "env": {"LIBSQL_URL": f"file:{GRAPH_DB}"},
}

memory_rag_params = {
    "command": "uvx",
    "args": ["mcp-server-qdrant"],
    "env": {
        "QDRANT_LOCAL_PATH": RAG_DB,
        "COLLECTION_NAME": "knowledge",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    },
}


def memory_graph_server():
    return MCPServerStdio(memory_graph_params, client_session_timeout_seconds=60)


def memory_rag_server():
    return MCPServerStdio(memory_rag_params, client_session_timeout_seconds=60)
