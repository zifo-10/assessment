from pydantic import BaseModel, Field
from typing import Optional, List
from pyobjectID import MongoObjectId

class LevelDTO(BaseModel):
    level: int
    difficulty: int

class TrainingDTO(BaseModel):
    training_name: str
    levels: list[LevelDTO]


class JobDTO(BaseModel):
    job_name: str = Field(..., title="Job Name", description="The name of the job")
    job_code: int = Field(..., title="Job Code", description="The code of the job")
    classification: str = Field(..., title="Classification", description="The classification of the job")
    trainings: list[TrainingDTO] = Field(..., title="Trainings", description="List of trainings associated with the job")

class GetJobDTO(JobDTO):
    id: MongoObjectId = Field(..., title="Job ID", description="The unique identifier for the job", alias="_id")