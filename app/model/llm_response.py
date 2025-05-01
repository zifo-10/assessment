from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    system: str
    user: str


class GeneratedDetails(BaseModel):
    learning_objectives: List[str] = Field(..., title="Learning Objectives")
    skills: List[str] = Field(..., title="Skills")
    key_responsibilities: List[str] = Field(..., title="Key Responsibilities")


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


class QuizQuestion(BaseModel):
    question: str = Field(..., description="The text of the quiz question")
    options: List[str] = Field(..., description="A list of four answer choices")
    correct_answer: str = Field(..., description="The correct answer text, must match one of the choices")
    explanation: str = Field(..., description="Explanation for the correct answer")
    question_type: QuestionType = Field(..., description="The type of the question")


class AssessmentQuiz(BaseModel):
    questions: List[QuizQuestion] = Field(..., description="List of generated quiz questions")


class AnswerOption(BaseModel):
    option_text: str
    explanation: str
    is_correct: bool


class ScenarioQuestion(BaseModel):
    scenario_description: str
    question_text: str
    options: List[AnswerOption]


class Analysis(BaseModel):
    gap: str = Field(..., description="The percentage of the gap")
    priority: str = Field(..., description="Priority level")
    ai_analysis: str = Field(..., description="Analysis text")
    title: str = Field(..., description="Summary in two or three words")


class AnalysisResult(BaseModel):
    feedback: List[Analysis] = Field(..., description="List of feedback items")