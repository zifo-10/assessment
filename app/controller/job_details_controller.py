from bson import ObjectId
from dotenv import load_dotenv
import os
from typing import Optional

from app.client.llm_client import OpenAIClient
from app.client.mongo_client import MongoDBClient
from app.model.llm_dto import PromptTemplate, AssessmentQuiz
from app.model.job_dto import JobDTO, GetJobDTO
from app.utils.utils import get_train_detail

# Load environment variables
load_dotenv()

# MongoDB connection setup
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
db_name = os.getenv('DB_NAME', 'assessment')
job_collection = os.getenv('COLLECTION_NAME', 'job')

# MongoDB and LLM clients
mongo_client = MongoDBClient(mongo_uri, db_name)
llm_client = OpenAIClient()


class JobDetailsController:
    def __init__(self, mongo_client: MongoDBClient, llm_client: OpenAIClient):
        self.mongo_client = mongo_client
        self.llm_client = llm_client

    def generate_job_detail(self, job_id: str, prompt_id: str, level: int = 0) -> AssessmentQuiz | None:
        """
        Generates job detail based on the specified job ID and prompt ID.
        """
        try:
            job_data = self.mongo_client.find_one(collection_name=job_collection, query={"_id": ObjectId(job_id)})
            if not job_data:
                print(f"Job with ID {job_id} not found.")
                return None
            print('Job Data:', job_data)
            job = GetJobDTO(**job_data)
            level_data = self._get_level_data(job, level)
            composed_data = {
                "job_name": job.job_name,
                "job_classification": job.classification,
                "training_details": level_data
            }

            prompt_doc = self.mongo_client.get_prompt_template(prompt_id=prompt_id)
            if not prompt_doc:
                print(f"Prompt with ID {prompt_id} not found.")
                return None

            prompt = self._generate_details_prompt(level_data=composed_data, level=level, prompt_template=prompt_doc)

            # Example LLM generation (commented for safety)
            llm_output = self.llm_client.generate_details(course_level=prompt)
            job_with_details = {
                "job_id": job.id,
                "skills": llm_output.skills,
                "learning_objectives": llm_output.learning_objectives,
                "key_responsibilities": llm_output.key_responsibilities,
            }
            self.mongo_client.insert_one(collection_name='job_details',
                                         document=job_with_details)
            assessment_prompt = self.mongo_client.get_prompt_template(prompt_id="6806673c950a52dabdb59689")
            formatted_assessment_prompt = self._generate_assessment_prompt(
                level_data=composed_data,
                level=level,
                prompt_template=assessment_prompt,
                job_with_details=job_with_details
            )
            assessment = self.llm_client.generate_assessment(formatted_assessment_prompt)
            insert_assessment = self.mongo_client.insert_one(
                collection_name='assessment',
                document={
                    "job_id": job.id,
                    "assessment": assessment.model_dump()
                }
            )
            return assessment

        except Exception as e:
            print(f"Failed to generate job detail: {e}")
            return None

    def _get_level_data(self, job: JobDTO, level: int) -> list[dict]:
        """
        Retrieves training details for the specified level.
        """
        training_details = []
        for training in job.trainings:
            try:
                difficulty = training.levels[level].difficulty
                timing = get_train_detail(difficulty)
                training_details.append({
                    "training_name": training.training_name,
                    "training_timing": timing,
                })
            except (IndexError, AttributeError):
                continue
        return training_details

    def _generate_details_prompt(self, level_data: dict, level: int, prompt_template: dict) -> PromptTemplate:
        """
        Constructs a PromptTemplate by replacing placeholders in the system prompt.
        """
        system_prompt = prompt_template["system"] \
            .replace("{job_name}", level_data["job_name"]) \
            .replace("{level}", str(level))
        user_input = str(level_data)
        return PromptTemplate(system=system_prompt, user=user_input)

    def _generate_assessment_prompt(self, level_data: dict, level: int,
                                    prompt_template: dict, job_with_details: dict) -> PromptTemplate:
        """
        Constructs a PromptTemplate for generating assessment questions.
        """
        system_prompt = prompt_template["system"] \
            .replace("{job_name}", level_data["job_name"]) \
            .replace("{level}", str(level))
        user_input = str(level_data) + str(job_with_details)
        return PromptTemplate(system=system_prompt, user=user_input)


# Example usage
if __name__ == "__main__":
    controller = JobDetailsController(mongo_client, llm_client)
    job_id = "68064030a146a64ef0b0d2cd"
    prompt_id = "680656c3950a52dabdb5967f"
    controller.generate_job_detail(job_id=job_id, prompt_id=prompt_id)
