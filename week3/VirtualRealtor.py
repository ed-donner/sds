#!/usr/bin/env python3
"""
Virtual Realtor - AI Digital Twin of Monika Trivedi
A Gradio-based chat interface for property inquiries and realtor services.
"""

from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from openai.types.responses import ResponseTextDeltaEvent
import gradio as gr
import os
import requests

# Load environment variables
load_dotenv(override=True)

# Configuration
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# Agent instructions
INSTRUCTIONS = """
You represent the AI Digital Twin of a human Realtor. That Realtor can be any licensed realtor named Monika Trivedi. 
You are friendly and amiable, and you introduce yourself as Your Virtual Realtor.
You let the user know that you represent Monika Trivedi of MonikaRealty and can answer questions on 
Monika's behalf. 
Monika Trivedi is a licenced realtor in the state of California. 
Monika loves what she does. She loves helping people find their dream home. 
She also helps people sell their homes. She specialized in upgrades. 
You chat with visitors on Monika's personal website. You answer questions about Kinjal's work any property 
they are inquiring about as Monika would. 
You will be provided with latest information about current properties in the market via various means. 
If you don't know the answer, say so.

You are a helpful assistant that can answer questions about the properties in the market.
use the latest information provided to you to answer the questions.
If asked about a property, gather the address of the property and use the property_info_tool to answer the questions.
If you don't know the answer, gather the address of the property, users contact information and send a push notification to Monika to tell her the question you couldn't answer, so that she can follow up 
and adds it to the knowledge base.
If you don't know the answer, say so.
"""


def send_push_notification(message: str) -> None:
    """Send a push notification via Pushover API."""
    payload = {
        "user": PUSHOVER_USER, 
        "token": PUSHOVER_TOKEN, 
        "message": message
    }
    try:
        response = requests.post(PUSHOVER_URL, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send push notification: {e}")


@function_tool
def book_appointment(message: str, name: str, phone: str, email: str, date: str, time: str) -> str:
    """Book a calendar appointment with the user for a property visit or a meeting using Google Drive calendar.

    Args:
        message: The address of the property to book an appointment for.
        name: The user's name.
        phone: The user's phone number.
        email: The user's email address.
        date: The date of the appointment.
        time: The time of the appointment.
    """
    notification_message = f"Appointment booking request from {name} ({phone}, {email}) for: {message}"
    send_push_notification(notification_message)
    return "Push notification sent for appointment booking"


@function_tool
def property_info_tool(message: str) -> str:
    """Find the property info for the given address by calling an API.

    Args:
        message: The address of the property to find the info for.
    """
    notification_message = f"Property info request for address: {message}"
    send_push_notification(notification_message)
    return "Push notification sent for property info request"


@function_tool
def push(message: str) -> str:
    """Send a text message as a push notification to Monika with this brief message.

    Args:
        message: The short text message to push to Monika.
    """
    send_push_notification(message)
    return "Push notification sent"


class VirtualRealtor:
    """Virtual Realtor agent class."""
    
    def __init__(self):
        """Initialize the Virtual Realtor agent."""
        self.agent = Agent(
            name="VirtualRealtor",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",  # Updated model name
            tools=[push, property_info_tool, book_appointment]
        )
    
    async def chat(self, message: str, history: list) -> str:
        """Handle chat messages with the agent.
        
        Args:
            message: The user's message.
            history: Previous conversation history.
            
        Returns:
            The agent's response.
        """
        messages = [{"role": prior["role"], "content": prior["content"]} for prior in history]
        messages += [{"role": "user", "content": message}]
        response = await Runner.run(self.agent, messages)
        return response.final_output
    
    async def chat_streamed(self, message: str, history: list):
        """Handle chat messages with streaming response.
        
        Args:
            message: The user's message.
            history: Previous conversation history.
            
        Yields:
            Streamed response chunks.
        """
        messages = [{"role": prior["role"], "content": prior["content"]} for prior in history]
        messages += [{"role": "user", "content": message}]
        response = Runner.run_streamed(self.agent, messages)
        reply = ""
        
        async for event in response.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                reply += event.data.delta
                yield reply


def create_interface(streaming: bool = False) -> gr.ChatInterface:
    """Create and return a Gradio chat interface.
    
    Args:
        streaming: Whether to use streaming responses.
        
    Returns:
        A configured Gradio ChatInterface.
    """
    virtual_realtor = VirtualRealtor()
    
    if streaming:
        return gr.ChatInterface(virtual_realtor.chat_streamed, type="messages")
    else:
        return gr.ChatInterface(virtual_realtor.chat, type="messages")


def main():
    """Main function to launch the Virtual Realtor interface."""
    print("Starting Virtual Realtor...")
    print("Make sure you have set PUSHOVER_USER and PUSHOVER_TOKEN in your .env file")
    
    # Check if required environment variables are set
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        print("Warning: PUSHOVER_USER and/or PUSHOVER_TOKEN not set in environment variables.")
        print("Push notifications will not work without these.")
    
    # Create and launch the interface
    interface = create_interface(streaming=True)  # Use streaming by default
    interface.launch()


if __name__ == "__main__":
    main()
