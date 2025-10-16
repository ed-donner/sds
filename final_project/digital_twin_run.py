from dotenv import load_dotenv
from agents import Agent, Runner
import gradio as gr
from pydantic import BaseModel, Field
from openai import OpenAI
import asyncio

load_dotenv(override=True)
openai = OpenAI()


def load_linkedin_profile():
    """Load the LinkedIn profile from a text file."""
    with open('./backend/api/data/linkedin_profile.txt', 'r') as file:
        return file.read()

class ChatResponse(BaseModel):
    llm_response: str = Field(description="The response from the LLM based on the LinkedIn profile")


async def chat(message, history):
    linkedin_profile = load_linkedin_profile()
    linkedin_profile = linkedin_profile + "\nAdditional info: Josh's favorite food is ice cream."
    
    # Put LinkedIn profile in the system prompt, not in every user message
    SYSTEM_PROMPT = f"""You are a digital twin of Joshua Janzen. Only answer questions about him. If you don't know the answer, just say you don't know.

Here is Joshua's LinkedIn profile and information:
{linkedin_profile}
"""
    
    agent = Agent(name="DigitalTwinAgent", instructions=SYSTEM_PROMPT, output_type=ChatResponse)
    
    # Build messages with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history - keep the original messages clean
    for msg in history:
        clean_msg = {
            "role": msg.get("role"),
            "content": msg.get("content")
        }
        messages.append(clean_msg)
    
    # Add current user message WITHOUT the LinkedIn profile (it's already in system prompt)
    messages.append({"role": "user", "content": message})

    response = await Runner.run(agent, messages)
    final_response = response.final_output_as(ChatResponse).llm_response

    return final_response

async def main():
    # Launch the Gradio interface
    gr.ChatInterface(chat, type="messages").launch()

if __name__ == "__main__":
    asyncio.run(main())