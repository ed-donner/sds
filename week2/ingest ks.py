import os
import glob
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from embeddings import get_embeddings
from dotenv import load_dotenv

MODEL = "gpt-4.1-nano"
db_name = "vector_db"
knowledge_base_path = "knowledge-base/*"

USE_HUGGINGFACE = False

load_dotenv(override=True)


def fetch_documents():
    folders = glob.glob("knowledge-base/*")
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            filename = os.path.basename(doc.metadata.get("source", ""))
            filename_without_ext = os.path.splitext(filename)[0]
            
            # Add doc metadata
            doc.metadata["doc_type"] = doc_type
            doc.metadata["filename"] = filename_without_ext
            documents.append(doc)
    return documents


def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=250)
    chunks = text_splitter.split_documents(documents)
    
    for chunk in chunks:
        doc_type = chunk.metadata.get("doc_type", "unknown")
        filename = chunk.metadata.get("filename", "unknown")
        
        # Add context that will be embedded
        context = f"Document Type: {doc_type} | Filename: {filename}\n\n"
        chunk.page_content = context + chunk.page_content
    
    return chunks


def create_embeddings(chunks):
    embeddings = get_embeddings()

    if os.path.exists(db_name):
        Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=db_name
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
