from pydantic import BaseModel, Field
from typing import List, Optional
from pyobjectID import PyObjectId


class AnswerOption(BaseModel):
    option_text: str
    explanation: str
    is_correct: bool
    option_id: PyObjectId

class ScenarioQuestion(BaseModel):
    level: int
    scenario_description: str
    question_text: str
    options: List[AnswerOption]
    parent_option_id: Optional[str] = Field(None, description="ID of the parent option")
    quiz_id: Optional[str] = Field(None, description="ID of the parent question")
    depth: int = Field(0, description="Depth in the scenario tree")
