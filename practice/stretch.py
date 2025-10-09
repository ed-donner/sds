#!/usr/bin/env python3
"""
Snarky Travel Agent - A Gradio app with OpenAI integration
"""

import os
import re
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Tuple, List

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sample cities with prices (in USD)
CITY_PRICES = {
    "paris": 850,
    "tokyo": 1200,
    "london": 750,
    "new york": 600,
    "sydney": 1400
}

def price_lookup_tool(city: str) -> Optional[int]:
    """
    Look up the price for a ticket to a specific city.
    
    Args:
        city: The city name to look up
        
    Returns:
        Price in USD if city is available, None otherwise
    """
    city_lower = city.lower().strip()
    return CITY_PRICES.get(city_lower)

def detect_city_in_message(message: str) -> Optional[str]:
    """
    Detect if a city is mentioned in the user's message.
    
    Args:
        message: The user's message
        
    Returns:
        City name if detected, None otherwise
    """
    message_lower = message.lower()
    
    # Check for each city in the message
    for city in CITY_PRICES.keys():
        if city in message_lower:
            return city.title()
    
    return None

def generate_travel_image(city: str, has_price: bool) -> str:
    """
    Generate a travel image using DALL-E based on city and price availability.
    
    Args:
        city: The city name
        has_price: Whether price is available for this city
        
    Returns:
        Image URL from DALL-E
    """
    if has_price:
        prompt = f"A beautiful, inviting travel poster for {city} with 'Price Available' text, showing iconic landmarks and attractions, vibrant colors, professional travel brochure style"
    else:
        prompt = f"A mysterious, dark travel poster for {city} with 'Price Not Available' text, showing the city in shadows, muted colors, professional travel brochure style"
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def get_snarky_response(message: str, city: Optional[str] = None, price: Optional[int] = None) -> str:
    """
    Get a snarky response from OpenAI based on the user's message.
    
    Args:
        message: The user's message
        city: Detected city (if any)
        price: Price for the city (if available)
        
    Returns:
        Snarky response from the assistant
    """
    system_prompt = """You are a snarky, sarcastic travel agent. You're knowledgeable but have a sharp wit and don't suffer fools gladly. 
    Keep your responses concise (2-3 sentences max) and inject some attitude. 
    If someone asks about ticket prices, mention the price if available, or tell them you don't know if it's not available.
    Be helpful but with a bit of sass."""
    
    if city and price is not None:
        user_prompt = f"User asked: '{message}' - They want to know about {city}. The price is ${price}. Respond snarkily."
    elif city and price is None:
        user_prompt = f"User asked: '{message}' - They want to know about {city} but we don't have pricing for that city. Respond snarkily."
    else:
        user_prompt = f"User asked: '{message}' - This is not about ticket prices. Respond to their question snarkily."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I'm having a bit of a technical meltdown right now. Try again later. (Error: {str(e)})"

def process_message(message: str, history: List[List[str]]) -> Tuple[str, str, str]:
    """
    Process the user's message and return response, image, and updated history.
    
    Args:
        message: The user's message
        history: Chat history
        
    Returns:
        Tuple of (response, image_url, updated_history)
    """
    if not message.strip():
        return "", None, history
    
    # Detect city in message
    city = detect_city_in_message(message)
    
    # Check if it's a price-related question
    price_related_keywords = ["price", "cost", "ticket", "fare", "how much", "expensive", "cheap"]
    is_price_question = any(keyword in message.lower() for keyword in price_related_keywords)
    
    # Get price if it's a price question and city is detected
    price = None
    if is_price_question and city:
        price = price_lookup_tool(city.lower())
    
    # Generate response
    response = get_snarky_response(message, city, price)
    
    # Generate image if city is detected
    image_url = None
    if city:
        has_price = price is not None
        image_url = generate_travel_image(city, has_price)
    
    # Update history
    updated_history = history + [[message, response]]
    
    return response, image_url, updated_history

def create_interface():
    """Create and configure the Gradio interface."""
    
    with gr.Blocks(title="Snarky Travel Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🧳 Snarky Travel Agent")
        gr.Markdown("*Your sarcastic guide to travel pricing*")
        
        with gr.Row():
            # Left side - Chat interface
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="Chat with your Snarky Travel Agent",
                    height=500,
                    show_label=True
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask about ticket prices or anything else...",
                        label="Your Message",
                        lines=2,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                gr.Markdown("### Available Cities for Pricing:")
                gr.Markdown("• Paris - $850  • Tokyo - $1,200  • London - $750  • New York - $600  • Sydney - $1,400")
            
            # Right side - Image display
            with gr.Column(scale=1):
                image_display = gr.Image(
                    label="Travel Destination",
                    height=500,
                    show_label=True
                )
        
        # Event handlers
        def handle_message(message, history):
            response, image_url, updated_history = process_message(message, history)
            return updated_history, image_url, ""
        
        # Connect the send button and Enter key
        send_btn.click(
            handle_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, image_display, msg_input]
        )
        
        msg_input.submit(
            handle_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, image_display, msg_input]
        )
    
    return demo

def main():
    """Main function to run the application."""
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file.")
        return
    
    print("🚀 Starting Snarky Travel Agent...")
    print("📋 Available cities for pricing: Paris, Tokyo, London, New York, Sydney")
    
    # Create and launch the interface
    demo = create_interface()
    demo.launch()

if __name__ == "__main__":
    main()
