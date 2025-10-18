from dotenv import load_dotenv
from agents import Agent, Runner
import gradio as gr

load_dotenv(override=True)

instructions = """
You represent the AI Digital Twin of a human called Ed Donner.
You are friendly and amiable, and you introduce yourself as Ed's Digital Twin.
Ed is the co-founder and CTO of AI startup Nebula.io.
If you don't know the answer, say so.
"""

agent = Agent(name="Twin", instructions=instructions, model="gpt-4.1-mini")


async def chat(message, history):
    messages = [{"role": prior["role"], "content": prior["content"]} for prior in history]
    messages += [{"role": "user", "content": message}]
    response = await Runner.run(agent, messages)
    return response.final_output


gr.ChatInterface(chat, type="messages").launch(inbrowser=True)
