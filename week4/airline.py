from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
import gradio as gr
import sqlite3
import traceback


load_dotenv(override=True)

MODEL = "gpt-4.1-mini"

instructions = "You are a helpful assistant for an Airline called FlightAI. "
instructions += "Use your tools to get ticket prices and calculate discounts. Trips to London have a 10% discount on the price. "
instructions += "Always be accurate. If you don't know the answer, say so."

DB = "prices.db"
initial_ticket_prices = {"london": 799, "paris": 899, "tokyo": 1400, "sydney": 2999}


with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)")
    for city, price in initial_ticket_prices.items():
        cursor.execute(f"INSERT OR IGNORE INTO prices (city, price) VALUES ('{city}', {price})")
    conn.commit()


@function_tool
def get_ticket_price(city: str) -> str:
    """Get the price of a ticket to a given city.

    Args:
        city: The city to get the price of a ticket to
    """
    print(f"TOOL CALLED: Getting price for {city}", flush=True)
    query = f"SELECT price FROM prices WHERE city = '{city.lower()}'"
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            return f"${result[0]}" if result else "Not found"
    except Exception as e:
        return f"Error: {traceback.format_exc()}"


@function_tool
def calculate(expr: str) -> str:
    """Evaluate a numeric expression - use this for example to make calculations about prices

    Args:
        expr: The expression to evaluate
    """
    print(f"TOOL CALLED: Calculating {expr}", flush=True)
    return str(eval(expr))


async def chat(message, history):
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages += [{"role": "user", "content": message}]
    agent = Agent(
        name="FlightAI", instructions=instructions, model=MODEL, tools=[get_ticket_price, calculate]
    )
    result = await Runner.run(agent, messages)
    return result.final_output


gr.ChatInterface(chat, type="messages").launch(inbrowser=True)
