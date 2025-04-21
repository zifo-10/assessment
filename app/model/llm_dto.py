from typing import List

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    system: str
    user: str

class GeneratedDetails(BaseModel):
    learning_objectives: List[str] = Field(..., title="Learning Objectives")
    skills: List[str] = Field(..., title="Skills")
    key_responsibilities: List[str] = Field(..., title="Key Responsibilities")



class QuizQuestion(BaseModel):
    question: str = Field(..., description="The text of the quiz question")
    choices: List[str] = Field(..., description="A list of four answer choices")
    correct_answer: str = Field(..., description="The correct answer text, must match one of the choices")
    explanation: str = Field(..., description="Explanation for the correct answer")

class AssessmentQuiz(BaseModel):
    questions: List[QuizQuestion] = Field(..., description="List of generated quiz questions")
