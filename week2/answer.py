from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from dotenv import load_dotenv
from embeddings import get_embeddings

load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
db_name = "vector_db"

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.

Context:
{context}
"""

vectorstore = Chroma(persist_directory=db_name, embedding_function=get_embeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
llm = ChatOpenAI(temperature=0, model_name=MODEL)


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)


async def answer_question(question: str) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    messages = [("system", SYSTEM_PROMPT), ("user", question)]
    prompt = ChatPromptTemplate.from_messages(messages)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = await rag_chain.ainvoke({"input": question})

    return response["answer"], response["context"]
