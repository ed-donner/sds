"""
MyTwin.py - AI Digital Twin Application
Based on Lab 3 - OpenAI Agents SDK with streaming

This script creates an AI Digital Twin that represents a person and can chat
with visitors on their website, answering questions about their career,
background, skills and experience.
"""

import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from openai.types.responses import ResponseTextDeltaEvent
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr
import requests
import os   
# Load environment variables
load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

# Global variable to hold the MyTwin instance for the push function
_twin_instance = None

@function_tool
def push(message: str) -> str:
    """Send a text message as a push notification to Kinjal with this brief message

    Args:
        message: The short text message to push to Kinjal.
    """
    if _twin_instance:
        _twin_instance.send_push_notification(message)
        return "Push notification sent"
    return "Push notification failed - twin instance not available"


class MyTwin:
    """
    AI Digital Twin class that represents a person and can chat with visitors.
    """
    
    def __init__(self, name="Kinjal Shah"):
        """
        Initialize the MyTwin with personal information.
        
        Args:
            name (str): The name of the person being represented
        """
        self.name = name
        self.agent = None
        self._setup_agent()
    
    def send_push_notification(self, message: str):
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        requests.post(pushover_url, data=payload)
    
    def _load_documents(self):
        """
        Load resume, LinkedIn profile, and summary from files.
        
        Returns:
            tuple: (resume_text, profile_text, summary_text)
        """
        # Load resume
        try:
            reader = PdfReader("info/KinjalShah_Resume.pdf")
            resume = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    resume += text
        except FileNotFoundError:
            print("Warning: Resume file not found. Using empty string.")
            resume = ""
        
        # Load LinkedIn profile
        try:
            reader = PdfReader("info/LinkedIn-Profile.pdf")
            profile = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    profile += text
        except FileNotFoundError:
            print("Warning: LinkedIn profile file not found. Using empty string.")
            profile = ""
        
        # Load summary
        try:
            with open("info/ks_summary.txt", "r", encoding="utf-8") as f:
                summary = f.read()
        except FileNotFoundError:
            print("Warning: Summary file not found. Using empty string.")
            summary = ""
        
        return resume, profile, summary
    
    def _create_instructions(self, resume, profile, summary):
        """
        Create the instructions for the AI agent.
        
        Args:
            resume (str): Resume text
            profile (str): LinkedIn profile text
            summary (str): Summary text
            
        Returns:
            str: Formatted instructions for the agent
        """
        instructions = f"""You represent the AI Digital Twin of a human called {self.name}. You are answering questions on {self.name}'s website, 
            particularly questions related to {self.name}'s career, background, skills and experience. 
            Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. 
            You are given a summary of {self.name}'s background,  LinkedIn profile and resumewhich you can use to answer questions. 
            Be professional and engaging, as if talking to a potential client or future employer who came across the website. 
            You are friendly and amiable, and you introduce yourself as {self.name}'s Digital Twin.
            {self.name} is Software Engineer Leader and a consultant.
            He loves coding and experimenting with LLMs as well as agentic AI. He is also a very good project manager and product manager.
            You chat with visitors on {self.name}'s personal website. You answer questions about {self.name}'s work.
            If you don't know the answer send a push notification to {self.name} to tell him the question you couldn't answer, so that he adds it to the knowledge base.
            """

        instructions += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{profile}\n\n## Resume:\n{resume}\n\n"
        instructions += f"With this context, please chat with the user, always staying in character as {self.name}."
        
        return instructions
    
    def _setup_agent(self):
        """Initialize the AI agent with instructions and model."""
        global _twin_instance
        _twin_instance = self  # Set the global instance so push function can access it
        
        resume, profile, summary = self._load_documents()
        instructions = self._create_instructions(resume, profile, summary)
        self.agent = Agent(name="Twin", instructions=instructions, model="gpt-4.1-mini", tools=[push])
    
    async def chat(self, message, history):
        """
        Chat function for non-streaming responses.
        
        Args:
            message (str): User's message
            history (list): Chat history
            
        Returns:
            str: Agent's response
        """
        messages = [{"role": prior["role"], "content": prior["content"]} for prior in history]
        messages += [{"role": "user", "content": message}]
        response = await Runner.run(self.agent, messages)
        return response.final_output
    
    async def chat_streaming(self, message, history):
        """
        Chat function for streaming responses.
        
        Args:
            message (str): User's message
            history (list): Chat history
            
        Yields:
            str: Partial response as it streams
        """
        messages = [{"role": prior["role"], "content": prior["content"]} for prior in history]
        messages += [{"role": "user", "content": message}]
        response = Runner.run_streamed(self.agent, messages)
        reply = ""
        async for event in response.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                reply += event.data.delta
                yield reply
    
    def launch_interface(self, streaming=True, share=False):
        """
        Launch the Gradio chat interface.
        
        Args:
            streaming (bool): Whether to use streaming responses
            share (bool): Whether to create a public link
        """
        chat_func = self.chat_streaming if streaming else self.chat
        gr.ChatInterface(chat_func, type="messages").launch(share=share)
    
    

def main():
    """Main function to run the MyTwin application."""
    print(f"Initializing AI Digital Twin...")
    
    # Create the twin
    twin = MyTwin()
    
    print(f"Digital Twin created for {twin.name}")
    print("Launching chat interface...")
    
    # Launch the interface
    twin.launch_interface(streaming=True, share=False)


if __name__ == "__main__":
    main()
