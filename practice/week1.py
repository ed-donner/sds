import gradio as gr
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "sydney": "$2999"}

def get_ticket_price(city):
    """Get ticket price for a city."""
    return ticket_prices.get(city.lower(), "City not found")

def generate_city_image(city):
    """Generate a clipart-style image of the city using DALL-E."""
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Simple clipart style illustration of {city.title()}, cartoon style, flat design, colorful, travel destination icon",
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        return None

def extract_city_from_message(message):
    """Extract city name from user message."""
    message_lower = message.lower()
    for city in ticket_prices.keys():
        if city in message_lower:
            return city
    return None

def chat_with_openai_stream(message, history):
    tools = [{
        "type": "function",
        "function": {
            "name": "get_ticket_price",
            "description": "Get ticket price for a destination city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name"}
                },
                "required": ["city"]
            }
        }
    }]
    
    messages = [
        {"role": "system", "content": "You are a snarky travel agent. Keep responses to one line maximum. Be sarcastic and witty. If a city is not found in the price database, respond with 'I don't know the price. Give another city.'"},
        {"role": "user", "content": message}
    ]
    
    detected_city = None
    full_response = ""
    
    # Check if we need to use tools first
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call.function.name == "get_ticket_price":
            city = eval(tool_call.function.arguments)["city"]
            price = get_ticket_price(city)
            detected_city = city
            full_response = f"Flight to {city.title()}: {price}"
    else:
        # Stream the response
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                yield full_response, detected_city
    
    # If no city detected through tools, try to extract from message
    if not detected_city:
        detected_city = extract_city_from_message(message)
    
    yield full_response, detected_city

def process_message(message, history):
    if not message.strip():
        return history, gr.update(), ""
    
    # Add user message to history
    history.append([message, ""])
    
    # Clear previous image and show loading
    yield history, gr.update(value=None, visible=True), "Loading..."
    
    # Stream the response
    for response, detected_city in chat_with_openai_stream(message, history):
        history[-1] = [message, response]
        yield history, gr.update(), "Loading..."
    
    # Generate image if city detected
    if detected_city:
        image_url = generate_city_image(detected_city)
        if image_url:
            yield history, gr.update(value=image_url), detected_city.title()
        else:
            yield history, gr.update(), f"Error loading {detected_city.title()} image"
    else:
        yield history, gr.update(value=None), ""

with gr.Blocks(title="Snarky Travel Agent") as app:
    gr.Markdown("# Snarky Travel Agent")
    
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(label="Ask about flights", placeholder="How much is a flight to Tokyo?")
        
        with gr.Column(scale=1):
            city_image = gr.Image(label="City Image", height=500)
            city_title = gr.Textbox(label="City", interactive=False)
    
    # Handle message submission with streaming and input clearing
    def submit_message(message, history):
        if not message.strip():
            return history, gr.update(), "", gr.update()
        
        # Process message and yield results
        for result in process_message(message, history):
            yield result + (gr.update(value=""),)  # Add empty input box update
    
    msg.submit(
        submit_message, 
        [msg, chatbot], 
        [chatbot, city_image, city_title, msg]
    )

if __name__ == "__main__":
    app.launch()
