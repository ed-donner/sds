# uv run playwright install chromium

import asyncio
from playwright.async_api import async_playwright
from agents import Agent, Runner, function_tool, trace


@function_tool
async def open_page_and_read_contents(url: str) -> str:
    """This tool opens a browser, navigates to the given URL, and returns the text on the page.
    Args:
        url: The URL of the page to open.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        text = await page.evaluate("() => document.body.innerText")
        await browser.close()
        return text


async def main() -> None:
    instructions = (
        "You are an Agent that can use your tool to read web pages, then you summarize them."
    )
    input = "Summarize https://www.cnn.com"
    agent = Agent(
        name="Browser Agent",
        model="gpt-4.1-mini",
        instructions=instructions,
        tools=[open_page_and_read_contents],
    )
    with trace("Browser Agent"):
        result = await Runner.run(agent, input)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
