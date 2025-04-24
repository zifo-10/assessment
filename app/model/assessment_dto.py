from typing import List, Union, Dict
from pyobjectID import MongoObjectId

from pydantic import BaseModel, Field


class GeneralQuestion(BaseModel):
    question: str = Field(..., title="Question", description="The text of the question")
    options: List[str] = Field(..., title="Choices", description="A list of answer choices")
    correct_answer: str = Field(..., title="Correct Answer",
                                description="The correct answer text, must match one of the choices")
    explanation: str = Field(..., title="Explanation", description="Explanation for the correct answer")
    question_type: str = Field(..., title="Question Type", description="The type of the question")


class ScenarioBaseOption(BaseModel):
    option_text: str = Field(..., title="Option Text", description="The text of the option")
    explanation: str = Field(..., title="Explanation", description="Explanation for the option")
    is_correct: bool = Field(..., title="Is Correct", description="Indicates if this option is correct")
    option_id: MongoObjectId = Field(..., title="Option ID", description="The id of the option")

class ScenarioBaseQuestion(BaseModel):
    scenario_description: str = Field(..., title="Scenario Description", description="The scenario description")
    question_text: str = Field(..., title="Question Text", description="The text of the question")
    options: List[ScenarioBaseOption] = Field(..., title="Options", description="List of answer options")
    question_type: str = Field(..., title="Question Type", description="The type of the question")

class AssessmentContent(BaseModel):
    questions: List[Union[GeneralQuestion, ScenarioBaseQuestion]]

class GetAssessmentDTO(BaseModel):
    id: MongoObjectId = Field(..., title="Assessment ID", description="The unique identifier for the assessment", alias="_id")
    job_id: str = Field(..., title="Job ID", description="The unique identifier for the job")
    level: int = Field(..., title="Level", description="The level of the assessment")
    assessment: AssessmentContent
