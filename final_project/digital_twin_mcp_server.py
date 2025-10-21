from mcp.server.fastmcp import FastMCP
import digital_twin_questions as questions

mcp = FastMCP("questions_server")


@mcp.tool()
async def get_questions_with_answer() -> str:
    """
    Retrieve from the database all the recorded questions where you have been provided with an official answer.

    Returns:
        A string containing the questions with their official answers.
    """
    return questions.get_questions_with_answer()


@mcp.tool()
async def get_questions_without_answer() -> str:
    """
    Retrieve from the database questions where there is not an answer.

    Returns:
        A string containing the questions without answers.
    """
    return questions.get_questions_without_answer()


@mcp.tool()
async def record_question_with_no_answer(question: str) -> str:
    """
    Record a question in the database for which you do not have an answer.

    Args:
        question (str): The question to be recorded.

    Returns:
        A string confirming the question has been recorded.
    """
    return questions.record_question_with_no_answer(question)


@mcp.tool()
async def record_question_with_answer(question: str, answer: str) -> str:
    """
    Record both a question AND its answer in the database when you provide an answer.
    Use this every time you answer a question about Joshua.

    Args:
        question (str): The question that was asked.
        answer (str): The answer you are providing.

    Returns:
        A string confirming the question and answer have been recorded.
    """
    return questions.record_question_with_answer(question, answer)


@mcp.tool()
async def update_answer_for_question(question_id: int, answer: str) -> str:
    """
    Update an existing question record with an official answer.
    Use this to add an answer to a previously unanswered question.

    Args:
        question_id (int): The ID of the question to update.
        answer (str): The official answer to be recorded.

    Returns:
        A string confirming the answer has been recorded.
    """
    return questions.record_answer_to_question(question_id, answer)


if __name__ == "__main__":
    mcp.run(transport="stdio")