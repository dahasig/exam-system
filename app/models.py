from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str
    level: str
    qtype: str
    question: str
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    correct_option: str = "A"


class Exam(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    token: str
    score: int = 0
    total: int = 0
    essay_count: int = 0
    suspicion: int = 0
    status: str = "started"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExamQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int
    question_id: int
    order_no: int


class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int
    question_id: int
    answer: str = ""
    essay: str = ""
    correct: bool = False
    seconds: int = 0


class ProctorEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int
    event: str
    details: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int
    image: str
    created_at: datetime = Field(default_factory=datetime.utcnow)