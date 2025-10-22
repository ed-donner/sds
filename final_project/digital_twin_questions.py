import sqlite3
from pathlib import Path

db_path = Path("memory") / Path("questions.db")
DB = db_path.absolute()


def record_question_with_no_answer(question: str) -> str:
    """Record a question without an answer."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (question, answer) VALUES (?, NULL)", (question,))
        conn.commit()
        return "Recorded question with no answer"


def record_question_with_answer(question: str, answer: str) -> str:
    """
    Record a question along with its answer in the database.
    
    Args:
        question (str): The question that was asked
        answer (str): The answer being provided
        
    Returns:
        str: Confirmation message
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        # Insert the question and answer into the database
        cursor.execute(
            "INSERT INTO questions (question, answer) VALUES (?, ?)", 
            (question, answer)
        )
        conn.commit()
        return f"Successfully recorded question and answer: '{question[:50]}...'"


def get_questions_without_answer() -> str:
    """Get all questions that don't have answers."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, question FROM questions WHERE answer IS NULL")
        rows = cursor.fetchall()
        if rows:
            return "\n".join(f"Question id {row[0]}: {row[1]}" for row in rows)
        else:
            return "No questions with no answer found"


def get_questions_with_answer() -> str:
    """Get all questions that have answers."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer FROM questions WHERE answer IS NOT NULL")
        rows = cursor.fetchall()
        if rows:
            return "\n".join(f"Question: {row[0]}\nAnswer: {row[1]}\n" for row in rows)
        else:
            return "No questions with answers found"


def record_answer_to_question(question_id: int, answer: str) -> str:
    """Update an existing question with an answer."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET answer = ? WHERE id = ?", (answer, question_id))
        conn.commit()
        return f"Recorded answer to question ID {question_id}"