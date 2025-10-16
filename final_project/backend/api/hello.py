from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent, Runner, function_tool
import json
from tavily import TavilyClient

hello = APIRouter()

load_dotenv(override=True)
openai = OpenAI()

@hello.get("/hello_world")
def hello_world():
    return {"message": f"Hello, You! {datetime.now().isoformat()}"}

@hello.get("/", response_class=HTMLResponse)
def hello_html():
    html_content = """
    <html>
        <head>
            <title>Hello HTML</title>
        </head>
        <body>
            <h1>Hello, World!</h1>
            <p>This is an HTML response.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@hello.get("/hello_llm")
def hello_llm():
    SYSTEM_PROMPT = "You are a helpful assistant that provides information about yourself."
    USER_PROMPT = "Can you tell me about your capabilities and provide some example use cases?"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ]

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=50,
        temperature=0.7,
    )

    response_message = response.choices[0].message
    return {"llm_response": response_message}

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "sydney": "$2999"}

def get_ticket_prices(city: str) -> str:
    if city.lower() in ticket_prices:
        return ticket_prices[city.lower()]
    else:
        return "Sorry, we don't have ticket prices for that city."

# Define the structured output format
class LLMCapabilities(BaseModel):
    """A Pydantic model to define the structure of the LLM's capabilities response."""
    
    main_response: str = Field(description="Main response describing what the LLM can do")
    capabilities: list = Field(description="List of specific capabilities")
    example_use_cases: list = Field(description="List of example use cases")
    is_helpful: bool = Field(description="Whether the LLM considers itself helpful")


@hello.get("/hello_llm_function_calling", response_model=LLMCapabilities)
def hello_llm_function_calling(city: str):
    SYSTEM_PROMPT = "you are an airline pricing expert. keep your answers very brief. if you don't know the answer, just say you don't know."
    USER_PROMPT = f"You are looking to fly to {city}. What is the ticket price?"

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_ticket_prices",
                "description": "Get the ticket price for flights to a specific city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The destination city name"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ]
    
    # First API call
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    
    # Check if the model wants to call a function
    tool_calls = response_message.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"Calling function {function_name} with args {function_args}")
            
            # Call the function
            if function_name == "get_ticket_prices":
                function_response = get_ticket_prices(**function_args)
                
                # Add function response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response
                })
        
        # Get final response from the model
        final_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        final_message = final_response.choices[0].message.content
    else:
        final_message = response_message.content

        # Return response matching LLMCapabilities schema
    return LLMCapabilities(
        main_response=final_message,
        capabilities=["Check flight prices", "Provide booking information"],
        example_use_cases=["Finding ticket prices to various cities"],
        is_helpful=True
    )

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


# start of llm agents with search, evaulation loops 


@function_tool
def get_tavily_search(search_term: str = "Minnesota Vikings news"):
    """Initialize Tavily search tool"""
    tavily_client = TavilyClient()
    response = tavily_client.search(search_term, num_results=5, time_range="day")
    return response


@hello.get("/hello_llm_agents_evaluator")
async def hello_llm_agents_evaluator(sports_team: str):
    fan_instructions = "You are a passionate sports fan who searches the web for the latest news about your favorite team."
    fan_input = """
    Search the web and look for some news about the {sports_team}.  Summarize the news you find in a few sentences.
    """

    evaluator_instructions = "You evaluate whether the story about the sports team."
    evaluator_input = "Evaluate the story and score it from 1 to 10 on how much it would cheer up a fan having a bad day."

    ## Now let's define 2 important Pydantic Objects to describe our Data
    class FanOutput(BaseModel):
        story: str = Field(description="A short story summary about the sports team.")
        url: str = Field(description="A url to a relevant article about the sports team.")

    class EvaluatorOutput(BaseModel):
        score: int = Field(description="A score from 1 to 10 on how much the story would cheer up a fan having a bad day.")
        reasoning: str = Field(description="A short reasoning about why you gave the score.")
        url: str = Field(description="A url to a relevant article about the sports team.")

        def is_amazingly_positive(self) -> bool:
            return self.score >= 9

    fan_agent = Agent(name="FanAgent", instructions=fan_instructions, tools=[get_tavily_search], output_type=FanOutput)
    result = await Runner.run(fan_agent, fan_input)

    evaluator_agent = Agent(name="EvaluatorAgent", instructions=evaluator_instructions, output_type=EvaluatorOutput)
    evaluator_input = evaluator_input + f"Here is the story: {result.final_output_as(FanOutput).story}"
    result = await Runner.run(evaluator_agent, evaluator_input)

    formatted_result = result.final_output_as(EvaluatorOutput)


    combine_attempts = []
    fan_latest = f"You were originally given the following story \n\n{fan_input}\n\n"
    remaining_attempts = 5
    while not formatted_result.is_amazingly_positive() and remaining_attempts:
        print(remaining_attempts)
        remaining_attempts -= 1
        fan_input += f"You responded with this story:\n\n{fan_input}\n\nYou received this feedback:\n\n{formatted_result}\n\n"
        fan_input += "Now respond with an improved story that adresses the feedback. Do not directly reference the feedback.\n\n"
        result = await Runner.run(fan_agent, fan_input)
        fan_output = result.final_output_as(FanOutput)
        result = await Runner.run(evaluator_agent, f"{evaluator_input}{fan_output.story}")
        print(f'for result atempt {3 - remaining_attempts}, got {result}')
        formatted_result = result.final_output_as(EvaluatorOutput)
        combine_attempts.append((fan_output, formatted_result))

    return {"llm_response": combine_attempts}