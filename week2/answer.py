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
You are a precise, concise assistant for Insurellm.
Use ONLY the provided context to answer. If the answer is not in the context, say "I don't know based on the provided documents."
When answering:
- Quote key facts verbatim where possible
- Include specific names, dates, and figures from the context
- Do not speculate or add facts not grounded in the context

Context:
{context}
"""

RAG_SYSTEM_PROMPT = """
You are a knowledgeable expert at converting a user question in to RAG friendly query.
Rewrite the user's question into a retrieval-friendly query that includes critical entities, dates, product names, 
and synonyms from the question. Keep it short and faithful to the original intent. Avoid adding new information. 
"""

vectorstore = Chroma(persist_directory=db_name, embedding_function=get_embeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
llm = ChatOpenAI(temperature=0, model_name=MODEL)


def raggify_query(question: str) -> str:
    """
    Convert a user question into a RAG-friendly format using the RAG_SYSTEM_PROMPT.
    """
    messages = [("system", RAG_SYSTEM_PROMPT), ("user", question)]
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    response =  chain.invoke({})
    return response.content


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    raggified_question =  raggify_query(question)
    print(f"Raggified question: {raggified_question}")
    return retriever.invoke(raggified_question)


async def answer_question(question: str) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    #raggified_question = await raggify_query(question)
    messages = [("system", SYSTEM_PROMPT), ("user", question)]
    prompt = ChatPromptTemplate.from_messages(messages)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = await rag_chain.ainvoke({"input": question})

    return response["answer"], response["context"]

