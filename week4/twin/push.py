import os
from dotenv import load_dotenv
import requests
from agents import function_tool

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


@function_tool
def push_notify_to_twin(message: str) -> str:
    """
    Send your human twin a push notification to let them know anything important - such as, if there's a new question that needs answering, or a new person that wants to get in touch,
    or anything else that you think they should know.

    Args:
        message (str): The message to send to your human twin.
    """
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)
    return "successfully sent push notification"
