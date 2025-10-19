from mcp.server.fastmcp import FastMCP
import questions

mcp = FastMCP("questions_server")


@mcp.tool()
async def get_questions_with_answer() -> str:
    """
    Retrieve from the database all the recorded questions where you have been provided with an official answer.

    Returns:
        A string containing the questions with their official answers.
    """
    return questions.get_questions_with_answer()


if __name__ == "__main__":
    mcp.run(transport="stdio")
