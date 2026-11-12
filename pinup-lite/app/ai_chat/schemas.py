from pydantic import BaseModel


class Question(BaseModel):
    question: str
    additional_context: str | None = None
    session_id: str | None = "default"
