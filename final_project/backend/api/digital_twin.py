from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent, Runner, function_tool
import json
from tavily import TavilyClient
import os 

digital_twin = APIRouter()

load_dotenv(override=True)
openai = OpenAI()

@digital_twin.get("/hello_world")
def hello_world():
    return {"message": f"Hello, You! {datetime.now().isoformat()}"}

'''

# start of using agents framework
@function_tool
def get_ticket_price_tool(city: str) -> str:
    """Get the ticket price for flights to a specific city.
    
    Args:
        city (str): The destination city name.
    """
    return get_ticket_prices(city)


@function_tool
def is_soccer_city(city: str) -> bool:
    """Check if a city is known for soccer.
    
    Args:
        city (str): The city name to check.
    """
    soccer_cities = ["london", "madrid", "barcelona", "manchester", "buenos aires"]
    return city.lower() in soccer_cities

class SoccerCity(BaseModel):
    is_soccer_city: bool = Field(description="Whether the city is known for soccer")
    description: str = Field(description="A short descpription of why a soccer city or not")
    airline_ticket_price: str = Field(description="The airline ticket price to the city. If unknown, say so.")


@hello.get("/hello_llm_agents")
async def hello_llm_agents(city: str):
    SYSTEM_PROMPT = "you are an airline pricing expert and also a soccer expert and must check if the city is a soccer city. keep your answers very brief. if you don't know the answer, just say you don't know."
    USER_PROMPT = f"You are looking to fly to {city}. What is the ticket price and let me know if its a soccer city?"
    agent = Agent(name="PricingAgent", instructions=SYSTEM_PROMPT, tools=[get_ticket_price_tool, is_soccer_city], output_type=SoccerCity)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ]
    response = await Runner.run(agent, messages)
    final_response = response.final_output_as(SoccerCity)
    return {"llm_response": final_response}
'''

# backend  frontend makefile
# (coding-tutorials) ➜  final_project git:(joshjanzen) ✗ cd backend 
# (coding-tutorials) ➜  backend git:(joshjanzen) ✗ ls
# __pycache__ api         data        main.py
# (coding-tutorials) ➜  backend git:(joshjanzen) ✗ cd data 
# (coding-tutorials) ➜  data git:(joshjanzen) ✗ ls
# linkedin_profile.txt

# from data.linkedin_profile.txt


def load_linkedin_profile():
    """Load the LinkedIn profile from a text file."""
    with open('./backend/api/data/linkedin_profile.txt', 'r') as file:
        return file.read()

class ChatResponse(BaseModel):
    llm_response: str = Field(description="The response from the LLM based on the LinkedIn profile")

@digital_twin.get("/chat_with_me")
async def chat_with_me(question: str):
    linkedin_profile = load_linkedin_profile()
    linkedin_profile = linkedin_profile + "josh favorite food is ice cream."
    SYSTEM_PROMPT = "You are a digital twin of Joshua Janzen. Only answer questions about him. If you don't know the answer, just say you don't know."
    USER_PROMPT = f"Based on the following LinkedIn profile: {linkedin_profile} Answer the following question: {question}"

    agent = Agent(name="DigitalTwinAgent", instructions=SYSTEM_PROMPT, output_type=ChatResponse)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ]

    response = await Runner.run(agent, messages)
    final_response = response.final_output_as(ChatResponse).llm_response
    return {"llm_response": final_response}


# gr.ChatInterface(chat, type="messages").launch()