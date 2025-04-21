from bson import ObjectId
from dotenv import load_dotenv
import os

from app.client.llm_client import OpenAIClient
from app.client.mongo_client import MongoDBClient
from app.model.llm_response import PromptTemplate, AssessmentQuiz
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
            scenario_base = self.scenario_base(
                level=level,
                level_data=composed_data,
                job_with_details=job_with_details
            )

            # self.mongo_client.insert_one(collection_name='job_details',
            #                              document=job_with_details)
            # pre_assessment = self.generate_pre_assessment(
            #     job=job,
            #     level=level,
            #     job_with_details=job_with_details,
            #     composed_data=composed_data
            # )
            return


        except Exception as e:
            print(f"Failed to generate job detail: {e}")
            return None

    def generate_pre_assessment(self, job: JobDTO, level: int, job_with_details: dict,
                                composed_data: dict) -> AssessmentQuiz:
        assessment_prompt = self.mongo_client.get_prompt_template(prompt_id="6806673c950a52dabdb59689")
        formatted_assessment_prompt = self._generate_assessment_prompt(
            level_data=composed_data,
            level=level,
            prompt_template=assessment_prompt,
            job_with_details=job_with_details
        )
        assessment = self.llm_client.generate_assessment(formatted_assessment_prompt)
        self.mongo_client.insert_one(
            collection_name='assessment',
            document={
                "job_id": job.id,
                "level": level,
                "assessment": assessment.model_dump()
            }
        )
        return assessment

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

    def scenario_base(self, level: int, level_data: dict, job_with_details: dict):
        scenario_base_prompt = self.mongo_client.get_prompt_template(prompt_id="68068d260a44ddefa5360a4b")
        follow_up_prompt = self.mongo_client.get_prompt_template(prompt_id="68068d450a44ddefa5360a4c")
        system_prompt = scenario_base_prompt["system"] \
            .replace("{job_name}", level_data["job_name"]) \
            .replace("{level}", str(level))
        user_input = str(level_data) + str(job_with_details)
        prompt_template = PromptTemplate(system=system_prompt, user=user_input)
        first_scenario = self.llm_client.generate_scenario_based(course_level=prompt_template)
        get_assessment = self.mongo_client.find_one(
            collection_name='assessment',
            query={"_id": ObjectId("68068b704bd19d9dc969e1b8")}
        )
        new_assessment = get_assessment['assessment']["questions"].append(first_scenario)

        self.mongo_client.update_one(collection_name="assessment",
                                     query={"_id": ObjectId("68068b704bd19d9dc969e1b8")},
                                     update={"assessment": new_assessment})
        depth = 0
        for option in first_scenario.options:
            follow_up_system = follow_up_prompt["system"] \
                .replace("{scenario}", first_scenario.scenario_description) \
                .replace("{answer_text}", option.option_text) \
                .replace("{depth}", str(depth + 1))
            user_answer = ""
            follow_up_prompt_template = PromptTemplate(system=follow_up_system, user=user_answer)
            follow_up = self.llm_client.generate_scenario_based(course_level=follow_up_prompt_template)


# Example usage
if __name__ == "__main__":
    controller = JobDetailsController(mongo_client, llm_client)
    job_id = "68064030a146a64ef0b0d2cd"
    prompt_id = "680656c3950a52dabdb5967f"
    controller.generate_job_detail(job_id=job_id, prompt_id=prompt_id)
