import sqlite3
from agents import function_tool

DB = "./memory/questions.db"

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )
    """)
    conn.commit()


@function_tool
def record_question_with_no_answer(question: str) -> str:
    """Record that a question has been asked that you have not been able to answer because
    you have no relevant knowledge to answer it. By recording it here, you ensure it will be answered at a later time.
    First you should use your tool to get all questions that have not been answered, so you have the right id to use.
    Then use this tool with the right id.

    Args:
        question: The question that was asked that you couldn't answer

    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (question, answer) VALUES (?, NULL)", (question,))
        conn.commit()
        return "This question has been recorded, and will be answered at a later time."


@function_tool
def record_answer_to_question(id: int, answer: str) -> str:
    """Record an answer to a question that has been provided by the admin user.

    Args:
        id: The id of the question that needed an answer
        answer: The answer to the question
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET answer = ? WHERE id = ?", (answer, id))
        conn.commit()
        return "The answer has been recorded."


def get_questions_with_no_answer() -> str:
    """Retrieve all the questions from the database that have not yet been answered and that require an answer"""

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, question FROM questions WHERE answer IS NULL")
        rows = cursor.fetchall()
        if rows:
            return "\n".join(f"- Question id {row[0]}: {row[1]}" for row in rows)
        else:
            return "- There are no questions without an answer at this time"


def get_questions_with_answer() -> str:
    """Retrieve all the questions that have been answered"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer FROM questions WHERE answer IS NOT NULL")
        rows = cursor.fetchall()
        return "\n".join(f"- Question: {row[0]}\nAnswer: {row[1]}" for row in rows)


def get_questions_tools() -> list:
    return [record_question_with_no_answer, record_answer_to_question]
