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
            history (list): Chat history in tuple format [(user_msg, bot_response), ...]
            
        Returns:
            str: Agent's response
        """
        messages = []
        for user_msg, bot_response in history:
            messages.append({"role": "user", "content": user_msg})
            if bot_response:
                messages.append({"role": "assistant", "content": bot_response})
        
        messages.append({"role": "user", "content": message})
        response = await Runner.run(self.agent, messages)
        return response.final_output
    
    async def chat_streaming(self, message, history):
        """
        Chat function for streaming responses.
        
        Args:
            message (str): User's message
            history (list): Chat history in tuple format [(user_msg, bot_response), ...]
            
        Yields:
            str: Partial response as it streams
        """
        messages = []
        for user_msg, bot_response in history:
            messages.append({"role": "user", "content": user_msg})
            if bot_response:
                messages.append({"role": "assistant", "content": bot_response})
        
        messages.append({"role": "user", "content": message})
        response = Runner.run_streamed(self.agent, messages)
        reply = ""
        async for event in response.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                reply += event.data.delta
                yield reply
    
    async def generate_professional_questions(self):
        """
        Generate 4 professional questions based on the resume and LinkedIn profile.
        
        Returns:
            str: Formatted list of 4 professional questions
        """
        resume, profile, summary = self._load_documents()
        
        prompt = f"""Based on the following resume, LinkedIn profile, and summary for {self.name}, 
        generate exactly 4 thoughtful, professional questions that a potential employer, 
        client, or business partner might ask during an interview or business meeting. 
        The questions should be relevant to {self.name}'s experience, skills, and background. Please keep the questions short and concise under 10 words.
        The questions should be in the form of a question, not a statement.
        The questions should be in the form of a question, not a statement.
        
        Resume: \n{resume}\n\n
        LinkedIn Profile: \n{profile}\n\n
        Summary: \n{summary}\n\n
        
        Please format your response as a numbered list of exactly 4 questions, 
        each on a new line, without any additional commentary or introduction."""
        
        instructions="You are a professional interviewer and business consultant who creates insightful, relevant questions based on someone's professional background."
        
        self.question_agent = Agent(name="Question Generator", instructions=instructions, model="gpt-4o-mini")
        messages = [{"role": "user", "content": prompt}]
        response = await Runner.run(self.question_agent, messages)
        
        return response.final_output
    
    def launch_interface(self, streaming=True, share=False):
        """
        Launch the Gradio chat interface with question generation button.
        
        Args:
            streaming (bool): Whether to use streaming responses
            share (bool): Whether to create a public link
        """
        chat_func = self.chat_streaming if streaming else self.chat
        
        with gr.Blocks(title=f"{self.name}'s Digital Twin") as demo:
            gr.Markdown(f"# Chat with {self.name}'s Digital Twin")
            gr.Markdown("Ask me anything about my career, experience, or background!")
            
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="Type your message here...", label="Message")
            
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear")
                question_btn = gr.Button("Generate Questions", variant="secondary")
            
            # Question buttons container (initially hidden)
            with gr.Row(visible=False) as question_row:
                gr.Markdown("**Click on a question to use it:**")
            
            with gr.Row(visible=False) as question_buttons_row:
                question_btn1 = gr.Button("", variant="outline", visible=False)
                question_btn2 = gr.Button("", variant="outline", visible=False)
                question_btn3 = gr.Button("", variant="outline", visible=False)
                question_btn4 = gr.Button("", variant="outline", visible=False)
            
            # Chat functionality with streaming
            def respond(message, history):
                if not message.strip():
                    return history, ""
                
                # Convert history to messages format for the agent
                messages = []
                for user_msg, bot_response in history:
                    messages.append({"role": "user", "content": user_msg})
                    if bot_response:
                        messages.append({"role": "assistant", "content": bot_response})
                
                # Add current message
                messages.append({"role": "user", "content": message})
                
                # Add empty response to history for streaming
                history.append([message, ""])
                
                # Use streaming
                import asyncio
                
                async def stream_response():
                    response = Runner.run_streamed(self.agent, messages)
                    reply = ""
                    
                    async for event in response.stream_events():
                        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                            reply += event.data.delta
                            # Update history with streaming response
                            history[-1][1] = reply
                            yield history, ""
                
                # Create a generator for streaming
                def stream_generator():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        async_gen = stream_response()
                        while True:
                            try:
                                yield loop.run_until_complete(async_gen.__anext__())
                            except StopAsyncIteration:
                                break
                    finally:
                        loop.close()
                
                # Yield from the generator for Gradio streaming
                for result in stream_generator():
                    yield result
            
            # Question generation functionality
            async def generate_questions():
                try:
                    questions_text = await self.generate_professional_questions()
                    # Parse questions from the text (assuming numbered list format)
                    questions = []
                    lines = questions_text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                            # Remove numbering/bullets and clean up
                            question = line
                            if line[0].isdigit():
                                # Remove "1. ", "2. ", etc.
                                question = line.split('.', 1)[1].strip() if '.' in line else line
                            elif line.startswith('•') or line.startswith('-'):
                                question = line[1:].strip()
                            
                            if question.endswith('?'):
                                questions.append(question)
                    
                    return questions
                except Exception as e:
                    return []
            
            def generate_and_show_questions():
                """Generate questions and show them as clickable buttons"""
                import asyncio
                questions = asyncio.run(generate_questions())
                
                if not questions:
                    return (
                        gr.update(visible=False),  # question_row
                        gr.update(visible=False),  # question_buttons_row
                        gr.update(visible=False),  # question_btn1
                        gr.update(visible=False),  # question_btn2
                        gr.update(visible=False),  # question_btn3
                        gr.update(visible=False),  # question_btn4
                    )
                
                # Show the question row and buttons
                updates = [
                    gr.update(visible=True),  # question_row
                    gr.update(visible=True),  # question_buttons_row
                ]
                
                # Update each button with a question (max 4)
                for i in range(4):
                    if i < len(questions):
                        updates.append(gr.update(visible=True, value=questions[i]))
                    else:
                        updates.append(gr.update(visible=False))
                
                return tuple(updates)
            
            def select_question(question_text):
                """Handle question selection"""
                return question_text
            
            # Event handlers
            msg.submit(respond, [msg, chatbot], [chatbot, msg])
            submit_btn.click(respond, [msg, chatbot], [chatbot, msg])
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
            
            # Question generation handler
            question_btn.click(
                generate_and_show_questions,
                outputs=[question_row, question_buttons_row, question_btn1, question_btn2, question_btn3, question_btn4]
            )
            
            # Question button click handlers
            question_btn1.click(select_question, inputs=[question_btn1], outputs=[msg])
            question_btn2.click(select_question, inputs=[question_btn2], outputs=[msg])
            question_btn3.click(select_question, inputs=[question_btn3], outputs=[msg])
            question_btn4.click(select_question, inputs=[question_btn4], outputs=[msg])
        
        demo.launch(share=share)
    
    

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
