import sqlite3
from agents import function_tool

DB = "./contacts.db"

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            notes TEXT            
        )
    """)
    conn.commit()


@function_tool
def record_new_person_to_get_in_touch(
    name: str = "Unknown",
    email: str = "Not given",
    phone: str = "Not given",
    notes: str = "No notes",
) -> str:
    """Record that someone would like to get in touch for the future.

    Args:
        name: The name of the person
        email: The email of the person
        phone: The phone number of the person
        notes: Any additional notes about the person, such as topics they are interested in, or any questions they asked that couldn't be answered
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (name, email, phone, notes) VALUES (?, ?, ?, ?)",
            (name, email, phone, notes),
        )
        conn.commit()
        return "This contact has been recorded."


@function_tool
def get_people_who_want_to_get_in_touch() -> str:
    """Retrieve all people recorded who would like to get in touch for the future"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, phone, notes FROM contacts")
        rows = cursor.fetchall()
        return "\n".join(
            f"Name: {row[0]}\nEmail: {row[1]}\nPhone: {row[2]}\nNotes: {row[3]}\n" for row in rows
        )
