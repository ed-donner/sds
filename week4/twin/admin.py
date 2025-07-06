from agents import Agent, Runner, trace
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
import gradio as gr
from mcp_servers import memory_graph_server, memory_rag_server
from questions import get_questions_tools
from contacts import get_people_who_want_to_get_in_touch
import asyncio
from resources import linkedin, summary, facts
import os
from questions import get_questions_with_no_answer

load_dotenv(override=True)

tools = get_questions_tools() + [get_people_who_want_to_get_in_touch]
MODEL = "gpt-4.1"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

full_name = facts["full_name"]
name = facts["name"]

instructions = f"""
# Your Role

You are an Administrator Agent.
You are part of an Agent Team that is responsible for answering questions about {full_name}, who goes by {name}.

## Important Context

Here is some basic information about {name}:
{facts}

Here is a summary of {name}:
{summary}

Here is the LinkedIn profile of {name}:
{linkedin}

## Your task

As Admin Agent, you are chatting directly with {full_name} who you should address as {name}. You are responsible for briefing {name} and updating your memory about {name}.

Here is a list of questions from users for {name} that have not been answered with their question id:

{get_questions_with_no_answer()}

## Your tools

You have access to the following memory related tools:
- Tools to manage the long term memory in a Graph database with entities and relationships. You should use these tools to record entity information you learn about {name} and other relevant people and places.
- Tools to manage memory using a Qdrant vector database. These tools let you look up and keep memories.

You should use both these tools together to record new information you learn; it's good to record information in both places.

If {name} offers to answer questions that have not been answered, you can mention those on your list.
Then if {name} is able to provide an answer, you should use your tool to record the answer to the question, and also update your graph memory and your Qdrant memory to reflect your new knowledge.

To be clear: every time {name} answers one of these questions, you should record the answer to the question being careful to specify the right question id,
and also update your graph memory and your Qdrant memory to reflect your new knowledge.

You also have tools to list people that have asked to get in touch with {name} that you can provide if asked.

## Instructions

Now with this context, proceed with your conversation with {name}.
"""

examples = [
    "Are there any questions that are not answered yet?",
    "Has anyone asked to get in touch with me?",
    "Please summarize your memory of me",
]


async def stream_response(messages, mcps):
    agent = Agent("Admin", instructions=instructions, model=MODEL, tools=tools, mcp_servers=mcps)
    result = Runner.run_streamed(agent, messages)
    reply = ""
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            reply += event.data.delta
            yield reply


async def chat(message, history):
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages += [{"role": "user", "content": message}]
    with trace("Admin"):
        async with memory_rag_server() as rag_server:
            async with memory_graph_server() as graph_server:
                mcps = [rag_server, graph_server]
                async for chunk in stream_response(messages, mcps):
                    yield chunk


def get_admin_interface():
    theme = gr.themes.Default(primary_hue="sky")
    title = "Digital Twin Admin"
    return gr.ChatInterface(chat, type="messages", examples=examples, theme=theme, title=title)


async def main():
    interface = await get_admin_interface()
    interface.launch(inbrowser=True, auth=[("admin", ADMIN_PASSWORD)])


if __name__ == "__main__":
    asyncio.run(main())
