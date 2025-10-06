import json
from pydantic import BaseModel, Field


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(description="Keywords that must appear in retrieved context")
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(description="Question category (e.g., direct_fact, spanning, temporal)")


def load_tests(filepath: str = "tests.jsonl") -> list[TestQuestion]:
    """Load test questions from JSONL file."""
    tests = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            tests.append(TestQuestion(**data))
    return tests
