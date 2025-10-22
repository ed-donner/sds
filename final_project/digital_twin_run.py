from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
import gradio as gr
from pydantic import BaseModel, Field
from openai import OpenAI
import asyncio
import sqlite3
import pandas as pd
from agents.mcp import MCPServerStdio
import os
import requests

# Load environment variables FIRST
load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

# Verify environment variables for push notifications
if not pushover_user or not pushover_token:
    print("⚠️  WARNING: PUSHOVER_USER or PUSHOVER_TOKEN not found in environment")
    print(f"   PUSHOVER_USER: {'✓' if pushover_user else '✗'}")
    print(f"   PUSHOVER_TOKEN: {'✓' if pushover_token else '✗'}")
else:
    print(f"✓ Push notification credentials loaded")

def send_push_notification(message: str):
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    try:
        response = requests.post(pushover_url, data=payload)
        print(f"Push notification response: {response.status_code}, {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False

@function_tool
def push(message: str) -> str:
    """Send a text message as a push notification to Josh with this brief message

    Args:
        message: The short text message to push to Josh
    """
    print(f"[PUSH TOOL CALLED] Sending message: {message}")
    success = send_push_notification(message)
    if success:
        return "Push notification sent successfully"
    else:
        return "Push notification failed to send"


openai = OpenAI()

# MCP Server params
params = {"command": "uv", "args": ["run", "digital_twin_mcp_server.py"]}

# Database setup
DB = "./memory/questions.db"
with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )
    ''')
    conn.commit()

def load_linkedin_profile():
    """Load the LinkedIn profile from a text file."""
    with open('./data/linkedin_profile.txt', 'r') as file:
        return file.read()

def get_database_contents():
    """Retrieve all records from the questions database."""
    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query("SELECT * FROM questions", conn)
        if df.empty:
            return pd.DataFrame(columns=["id", "question", "answer"])
        return df

class ChatResponse(BaseModel):
    user_question: str = Field(description="The question asked by the user")
    is_answerable: bool = Field(description="Indicates if the question was answerable based on existing data")
    answer: str = Field(description="The answer to the user's question, if available")
    llm_response: str = Field(description="The response from the LLM based on the LinkedIn profile")


async def chat(message, history):
    linkedin_profile = load_linkedin_profile()
    linkedin_profile = linkedin_profile + "\nAdditional info: Josh's favorite food is ice cream."
    

    # Let the agent naturally decide when to use tools
    SYSTEM_PROMPT = f"""
    You are a digital twin of this user.

    LinkedIn Profile:
    {linkedin_profile}

    TOOLS YOU CAN CALL (via MCP):
    - get_questions_with_answer() → recall known Q&A
    - get_questions_without_answer() → list unanswered Qs
    - record_question_with_answer(question, answer) → store new knowledge
    - record_question_with_no_answer(question) → store an unknown as unanswered

    TURN CONTRACT — FOLLOW EXACTLY:
    1) Read the latest user message as the variable `user_question`.
    2) Decide if you can answer from the profile or prior data.
    - If yes, set `is_answerable=True` and put the final answer string in `answer`.
    - If no, set `is_answerable=False` and leave `answer` empty.
    3) You MUST call EXACTLY ONE of the two logging tools every turn BEFORE giving your final reply:
    - If `is_answerable=True` → call record_question_with_answer(question=user_question, answer=answer)
    - Else → call record_question_with_no_answer(question=user_question)
    4) After the tool call finishes, produce your final message to the user in `llm_response`.
    5) Do not skip step 3 under any circumstance. Do not call both tools.
    6) If is_answerable=False, send a push notification with the tool to Josh to tell him the question you couldn't answer, so that he adds it to the knowledge base.

    Output must conform to the ChatResponse schema. Do not fabricate facts.
    """

    
    # Initialize MCP server and agent with it
    with trace("digital_twin_run_chat"):
        async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
            agent = Agent(
                name="DigitalTwinAgent",
                instructions=SYSTEM_PROMPT,
                output_type=ChatResponse,
                mcp_servers=[server],
                tools=[push],
                model="gpt-4o-mini"  
            )

            # Build messages with system prompt
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add conversation history
            for msg in history:
                clean_msg = {
                    "role": msg.get("role"),
                    "content": msg.get("content")
                }
                messages.append(clean_msg)

            # Add current user message with explicit instruction
            messages.append({"role": "user", "content": message})

            response = await Runner.run(agent, messages)
            final_response = response.final_output_as(ChatResponse).llm_response

            return final_response


async def test_mcp_connection():
    """Test function to verify MCP server is working"""
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        agent = Agent("TestAgent", model="gpt-4o-mini", mcp_servers=[server])
        task = "What are the questions for which you have an official recorded answer?"
        response = await Runner.run(agent, task)
        print("MCP Test Response:", response)
        return response


def refresh_database_view():
    """Refresh and return the current database contents."""
    return get_database_contents()


async def main():
    # Test MCP connection on startup
    print("Testing MCP connection...")
    try:
        await test_mcp_connection()
        print("MCP server connected successfully!")
    except Exception as e:
        print(f"Warning: MCP server test failed: {e}")
    
    # Create Gradio interface with tabs
    with gr.Blocks(title="Digital Twin") as demo:
        gr.Markdown("# Digital Twin")
        gr.Markdown("Ask questions about this user, and the system will track what it knows and doesn't know.")

        with gr.Tabs():
            with gr.Tab("Chat"):
                chat_interface = gr.ChatInterface(
                    chat, 
                    type="messages",
                    examples=[
                        "What is this user's favorite food?",
                        "Where did this user go to university?",
                        "What is this user's current role?",
                        "What are this user's hobbies?"
                    ]
                )
            
            with gr.Tab("Database Viewer"):
                gr.Markdown("## Questions Database")
                gr.Markdown("View all recorded questions and answers")
                
                refresh_btn = gr.Button("🔄 Refresh Database")
                database_table = gr.Dataframe(
                    value=get_database_contents(),
                    headers=["ID", "Question", "Answer"],
                    interactive=False,
                    wrap=True
                )
                
                refresh_btn.click(
                    fn=refresh_database_view,
                    outputs=database_table
                )
                
                # Auto-refresh every 5 seconds using Timer
                gr.Timer(value=5).tick(
                    fn=refresh_database_view,
                    outputs=database_table
                )
    
    # Launch the interface
    print("Launching Gradio interface...")
    demo.launch()


if __name__ == "__main__":
    asyncio.run(main())
