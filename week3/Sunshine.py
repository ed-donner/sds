import dotenv
from  pypdf import PdfReader
from agents import Agent, Runner, function_tool
from typing import Iterable
from time import time
import gradio as gr
from openai.types.responses import ResponseTextDeltaEvent
import urllib.parse
import urllib.request
import json
pdf_to_text=PdfReader('Salma Wahwah - Resume-2025.pdf')

context=''

for i, page in enumerate(pdf_to_text.pages):
   context+=page.extract_text()

   import os
dotenv.load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Configuration thresholds
LOW_SCORE = 0.5  # Adjust based on your needs
LOW_PROB = 0.6   # Adjust based on your needs

FALLBACK_MARKERS = {"i don't know", "not sure", "cannot answer"}

# Alert rate limiting (optional)
_last_alert_time = {}
ALERT_COOLDOWN = 300  # 5 minutes between similar alerts

instructions = f"""
You represent the AI Digital Twin of a human called Salma Wahwah.
You are friendly and amiable, and you introduce yourself as Salma's Digital Twin.
{context}
Salma also loves Grilled wagyu steak. Yummy Yummy!!! num num
You chat with visitors on Salma's personal website. You answer questions about Salma's work.
If you don't know the answer, say "I am not sure".
"""

def _should_alert(key: str) -> bool:
    now = time()
    last = _last_alert_time.get(key, 0)
    if now - last >= ALERT_COOLDOWN:
        _last_alert_time[key] = now
        return True
    return False

    

@function_tool
def notify_telegram(title: str, body: str, silent: bool = False) -> dict:
    """
    Send a short alert message to my Telegram when the agent is unsure.
    
    Args:
        title: The title/header of the message (will be bolded)
        body: The main message content
        silent: Whether to send silently (no notification sound)
    
    Returns:
        dict: Response from Telegram API
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"error": "Telegram credentials not configured", "success": False}
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = f"*{title}*\n{body}"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": bool(silent),
    }
    
    encoded = urllib.parse.urlencode(data).encode()
    
    try:
        with urllib.request.urlopen(url, data=encoded, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e), "success": False}
agent=Agent(name='Twin', instructions=instructions,tools=[notify_telegram])




def handle_turn(user_query: str):
    """
    Handle a user query and send Telegram alerts when confidence is low.
    
    Args:
        user_query: The user's question or input
        
    Returns:
        The agent's result object
    """
    # Get agent's response
    result = agent.answer(user_query)
    text = result.text
    
    # Extract confidence metrics
    low_conf = getattr(result, "confidence", None)
    top_score = getattr(result, "top_retrieval_score", None)
    
    # Check if response indicates uncertainty
    is_fallback_text = any(m in text.lower() for m in FALLBACK_MARKERS)
    is_low_conf = (
        (top_score is not None and top_score < LOW_SCORE)
        or (low_conf is not None and low_conf < LOW_PROB)
    )
    
    # Send alert if uncertain and not rate-limited
    if (is_fallback_text or is_low_conf) and _should_alert(user_query.strip().lower()):
        try:
            notify_telegram(
                title="🚨 Agent doesn't know",
                body=f"Query: {user_query}\nPreview: {text[:400]}",
                silent=False  # Set to True for silent notifications
            )
            print(f"[Alert sent] Low confidence response for: {user_query[:50]}...")
        except Exception as e:
            # Log error but don't break user flow
            print(f"[notify_telegram error] {e}")
    
    return result

async def chat(message, history):
    messages = [{"role": prior["role"], "content": prior["content"]} for prior in history]  
    messages += [{"role": "user", "content": message}]
    response = Runner.run_streamed(agent, messages)
    reply = ""
    async for event in response.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            reply += event.data.delta
            yield reply

gr.ChatInterface(chat, type="messages").launch()