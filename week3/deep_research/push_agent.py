import os

import requests
from agents import Agent, function_tool, ModelSettings

pushover_user = os.environ.get("PUSHOVER_USER")
pushover_token = os.environ.get("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


@function_tool
def push(message: str):
    """Send a push notification with this brief message

    Args:
        message: The message to send to the user as a push notification.
    """
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)
    return {"status": "success"}


INSTRUCTIONS = """You are a member of a research team and will be provided with a short summary of a report.
When you receive the report summary, you send a push notification to the user using your tool, informing them that research is complete,
and including the report summary you receive"""


push_agent = Agent(
    name="Push agent",
    instructions=INSTRUCTIONS,
    tools=[push],
    model="gpt-4.1-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
