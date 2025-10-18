from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
import asyncio

load_dotenv(override=True)

params = {"command": "npx", "args": ["@playwright/mcp@latest"]}

instructions = "You use your tools to browse the internet to accomplish your task."
task = "What's the headline news story on CNN right now?"


async def get_headline():
    async with MCPServerStdio(params=params, client_session_timeout_seconds=120) as browser:
        agent = Agent(
            name="Researcher",
            instructions=instructions,
            model="gpt-5-mini",
            mcp_servers=[browser],
        )
        result = await Runner.run(agent, task)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(get_headline())
