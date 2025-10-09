from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from dotenv import load_dotenv
from embeddings import get_embeddings
from pathlib import Path

load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
db_name = "vector_db"

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.

Summary of all content:
{summary}

Context:
{context}
"""

vectorstore = Chroma(persist_directory=db_name, embedding_function=get_embeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 30})
llm = ChatOpenAI(temperature=0, model_name=MODEL)


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)


def load_latest_summary() -> str:
    """
    Load the latest summary file from the knowledge-base/summary folder.
    """
    summary_dir = Path("knowledge-base/summary")
    summary_files = sorted(summary_dir.glob("*.md"))
    if summary_files:
        latest_summary = summary_files[-1]
        return latest_summary.read_text()
    return "No summary available."


async def answer_question(question: str) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    summary_content = load_latest_summary()
    system_prompt_with_summary = SYSTEM_PROMPT.format(summary=summary_content, context="{context}")
    
    messages = [("system", system_prompt_with_summary), ("user", question)]
    prompt = ChatPromptTemplate.from_messages(messages)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = await rag_chain.ainvoke({"input": question})

    return response["answer"], response["context"]
