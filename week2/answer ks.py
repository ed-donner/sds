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

RAG_SYSTEM_PROMPT = """
You are a knowledgeable expert at converting a user question in to something that is RAG friendly.
A user enters a quesiton anything regarding a given company. Your job is to translate the user entered 
question in to someting that we can use to query RAG f RAG Vector DB.
Please keep the size of the response roughtly the same as the prompt. 

"""

vectorstore = Chroma(persist_directory=db_name, embedding_function=get_embeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 12})
llm = ChatOpenAI(temperature=0, model_name=MODEL)


async def raggify_query(question: str) -> str:
    """
    Convert a user question into a RAG-friendly format using the RAG_SYSTEM_PROMPT.
    """
    messages = [("system", RAG_SYSTEM_PROMPT), ("user", question)]
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    response = await chain.ainvoke({})
    return response.content


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)


async def answer_question(question: str) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    raggified_question = await raggify_query(question)
    messages = [("system", SYSTEM_PROMPT), ("user", raggified_question)]
    prompt = ChatPromptTemplate.from_messages(messages)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = await rag_chain.ainvoke({"input": question})

    return response["answer"], response["context"]

