from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import acompletion, completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import litellm
from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
import os


# MODEL = "gpt-4.1-nano"
MODEL = "groq/openai/gpt-oss-120b"
db_name = "preprocessed_db"
collection_name = "docs"
embedding_model = "text-embedding-3-large"
load_dotenv(override=True)
openai = OpenAI()
groq_api_key = os.getenv("GROQ_API_KEY")

chroma = PersistentClient(path=db_name)
collection = chroma.get_or_create_collection(collection_name)


SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Use the given context to provide a comprehensive answer to the user's question.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


@retry(
    wait=wait_exponential(multiplier=1, min=10, max=240),
    stop=stop_after_attempt(10),
)
def rerank(question, chunks):
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a vector search of a knowledge base.
The chunks are provided in the order they were retrieved from the vector search; they should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks based on relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nPlease rank all the chunks of text based on relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    print(order)
    return [chunks[i - 1] for i in order]


def fetch_context(question, k=10):
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    results = collection.query(query_embeddings=[query], n_results=k)
    chunks = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    return rerank(question, chunks)


def make_context(chunks):
    result = ""
    for chunk in chunks:
        result += f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}\n\n"
    return result


def get_summaries():
    paths = [
        Path("knowledge-base") / "company" / "about.md",
        Path("knowledge-base") / "company" / "overview.md",
        Path("summaries") / "contracts.md",
        Path("summaries") / "employees.md",
        Path("summaries") / "products.md",
    ]
    summaries = ""
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            summaries += "Summary document: " + path.name + "\n\n"
            summaries += f.read() + "\n\n"
    return summaries


def make_rag_messages(question, chunks):
    context = make_context(chunks)
    system_prompt = f"""
{SYSTEM_PROMPT}

For context, here are specific extracts from the Knowledge Base that might be directly relevant to the question:

{context}

Here are general summaries of the company's Knowledge Base:

{get_summaries()}

With this context, please answer the question. Be accurate, relevant and complete.

If you need to search the Knowledge Base for specific information based on a single keyword, use the document_search_for_keyword tool.

In order to ensure you score well for completeness, the last sentence of your answer must begin "For completeness, " or "To provide a complete answer, " and add additional information from the context that's relevant to the question, rounding out the answer.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nPlease reply with your answer to the user, giving an accurate, relevant and complete answer based on the context provided."
    return system_prompt, user_prompt


def fetch_documents():
    base_path = Path("knowledge-base")
    documents = []

    for folder in base_path.iterdir():
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

    print(f"Loaded {len(documents)} documents")
    return documents


@function_tool
def document_search_for_keyword(keyword: str) -> str:
    """
    Search the knowledge base (case insensitive) for documents that contain the given keyword. The keyword should be something specific, like the name of a University.

    Args:
        keyword: The keyword to search for.

    Returns:
        The text in up to 3 documents that contain the keyword.
    """
    documents = fetch_documents()
    found = []
    for document in documents:
        if keyword.lower() in document["text"].lower():
            found.append(document["text"])
    print(f"TOOL USE: Found {len(found)} documents containing the keyword: {keyword}")
    if found:
        return "\n\n".join(found[:3])
    else:
        return "No documents found containing the keyword."


@retry(
    retry=retry_if_exception_type(litellm.exceptions.RateLimitError),
    wait=wait_exponential(multiplier=1, min=10, max=240),
    stop=stop_after_attempt(10),
)
async def answer_question(question: str) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    chunks = fetch_context(question)
    system_prompt, user_prompt = make_rag_messages(question, chunks)
    litellm_model = LitellmModel(model=MODEL, api_key=groq_api_key)
    agent = Agent(
        name="Answerer",
        model=litellm_model,
        instructions=system_prompt,
        tools=[document_search_for_keyword],
    )
    response = await Runner.run(agent, user_prompt)
    return response.final_output, chunks
