from dotenv import load_dotenv
from agents import Agent, Runner, trace
import gradio as gr
from pydantic import BaseModel, Field
from openai import OpenAI
import asyncio
import sqlite3
import pandas as pd
from agents.mcp import MCPServerStdio


load_dotenv(override=True)
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
    llm_response: str = Field(description="The response from the LLM based on the LinkedIn profile")
    should_record: bool = Field(description="Indicates if the response should be recorded in the database")
    is_answerable: bool = Field(description="Indicates if the question was answerable based on existing data")


async def chat(message, history):
    linkedin_profile = load_linkedin_profile()
    linkedin_profile = linkedin_profile + "\nAdditional info: Josh's favorite food is ice cream."
    

    # Let the agent naturally decide when to use tools
    SYSTEM_PROMPT = f"""You are a digital twin of Joshua Janzen.

    LinkedIn Profile:
    {linkedin_profile}

    You have access to tools that let you:
    - Check previously recorded answers
    - Record new Q&A pairs when appropriate

    Use these tools when helpful, but answer from the profile when you can."""
    
    # Initialize MCP server and agent with it
    with trace("digital_twin_run_chat"):
        async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
            agent = Agent(
                name="DigitalTwinAgent",
                instructions=SYSTEM_PROMPT,
                output_type=ChatResponse,
                mcp_servers=[server],
                model="gpt-4o"  # Using a more capable model for better tool use
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
            user_message = f"{message}\n\n[Remember: Check recorded answers first using get_questions_with_answer()]"
            messages.append({"role": "user", "content": user_message})

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
    with gr.Blocks(title="Joshua's Digital Twin") as demo:
        gr.Markdown("# Joshua Janzen's Digital Twin")
        gr.Markdown("Ask questions about Joshua, and the system will track what it knows and doesn't know.")
        
        with gr.Tabs():
            with gr.Tab("Chat"):
                chat_interface = gr.ChatInterface(
                    chat, 
                    type="messages",
                    examples=[
                        "What is Josh's favorite food?",
                        "Where did Josh go to university?",
                        "What is Josh's current role?",
                        "What are Josh's hobbies?"
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