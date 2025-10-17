import sqlite3
from pathlib import Path

db_path = Path("memory") / Path("questions.db")
DB = db_path.absolute()


def record_question_with_no_answer(question: str) -> str:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (question, answer) VALUES (?, NULL)", (question,))
        conn.commit()
        return "Recorded question with no answer"


def get_questions_with_no_answer() -> str:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, question FROM questions WHERE answer IS NULL")
        rows = cursor.fetchall()
        if rows:
            return "\n".join(f"Question id {row[0]}: {row[1]}" for row in rows)
        else:
            return "No questions with no answer found"


def get_questions_with_answer() -> str:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer FROM questions WHERE answer IS NOT NULL")
        rows = cursor.fetchall()
        return "\n".join(f"Question: {row[0]}\nAnswer: {row[1]}\n" for row in rows)


def record_answer_to_question(id: int, answer: str) -> str:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET answer = ? WHERE id = ?", (answer, id))
        conn.commit()
        return "Recorded answer to question"
