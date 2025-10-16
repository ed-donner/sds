from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from datetime import datetime
import time
from pydantic import BaseModel, Field

hello = APIRouter()

# Define the structured output format
class LLMCapabilities(BaseModel):
    """A Pydantic model to define the structure of the LLM's capabilities response."""
    
    main_response: str = Field(description="Main response describing what the LLM can do")
    capabilities: list = Field(description="List of specific capabilities")
    example_use_cases: list = Field(description="List of example use cases")
    is_helpful: bool = Field(description="Whether the LLM considers itself helpful")

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

