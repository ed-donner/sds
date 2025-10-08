from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

USE_HUGGINGFACE = True
MODEL = "all-MiniLM-L6-v2"


def get_embeddings():
    if USE_HUGGINGFACE:
        return HuggingFaceEmbeddings(model_name=MODEL)
    else:
        return OpenAIEmbeddings()
