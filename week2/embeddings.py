from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

USE_HUGGINGFACE = False
# MODEL = "all-MiniLM-L6-v2"
MODEL = "BAAI/bge-base-en-v1.5" 
OPENAI_MODEL = "text-embedding-3-large"


def get_embeddings():
    if USE_HUGGINGFACE:
        return HuggingFaceEmbeddings(model_name=MODEL)
    else:
        return OpenAIEmbeddings(model=OPENAI_MODEL)
