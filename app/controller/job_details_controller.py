from bson import ObjectId
from dotenv import load_dotenv
import os
import logging

from app.client.llm_client import OpenAIClient
from app.client.mongo_client import MongoDBClient
from app.model.llm_response import PromptTemplate, AssessmentQuiz
from app.model.job_dto import JobDTO, GetJobDTO
from app.utils.utils import get_train_detail

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
db_name = os.getenv('DB_NAME', 'assessment')
job_collection = os.getenv('COLLECTION_NAME', 'job')

# Mongo and LLM clients
mongo_client = MongoDBClient(mongo_uri, db_name)
llm_client = OpenAIClient()


class JobDetailsController:
    def __init__(self, mongo_client: MongoDBClient, llm_client: OpenAIClient):
        self.mongo_client = mongo_client
        self.llm_client = llm_client

    def generate_job_detail(self, job_id: str, prompt_id: str, level: int = 0) -> AssessmentQuiz | None:
        try:
            job = self._get_job(job_id)
            if not job:
                return None
            level_data = self._get_level_data(job, level)
            composed_data = {
                "job_name": job.job_name,
                "job_classification": job.classification,
                "training_details": level_data
            }

            prompt_doc = self.mongo_client.get_prompt_template(prompt_id=prompt_id)
            if not prompt_doc:
                logger.error(f"Prompt with ID {prompt_id} not found.")
                return None

            prompt = self._generate_details_prompt(level_data=composed_data, level=level, prompt_template=prompt_doc)
            llm_output = self.llm_client.generate_details(course_level=prompt)
            print(llm_output)
            job_with_details = {
                "job_id": job.id,
                "skills": llm_output.skills,
                "learning_objectives": llm_output.learning_objectives,
                "key_responsibilities": llm_output.key_responsibilities,
            }

            # Generate the pre-assessment and retrieve the inserted quiz ID
            assessment, quiz_id = self.generate_pre_assessment(job, level, job_with_details, composed_data)

            # Pass the quiz ID to scenario_base
            self.scenario_base(level, composed_data, job_with_details, quiz_id)
            return assessment
        except Exception as e:
            logger.exception(str(e))
            return None

    def generate_pre_assessment(self, job: JobDTO, level: int, job_with_details: dict,
                                composed_data: dict) -> tuple[AssessmentQuiz, str]:
        assessment_prompt = self.mongo_client.get_prompt_template(prompt_id="6806673c950a52dabdb59689")
        formatted_assessment_prompt = self._generate_assessment_prompt(
            level_data=composed_data,
            level=level,
            prompt_template=assessment_prompt,
            job_with_details=job_with_details
        )
        assessment = self.llm_client.generate_assessment(formatted_assessment_prompt)
        insert_result = self.mongo_client.insert_one(
            collection_name='assessment',
            document={
                "job_id": job.id,
                "level": level,
                "assessment": assessment.model_dump()
            }
        )
        return assessment, str(insert_result)

    def scenario_base(self, level: int, level_data: dict, job_with_details: dict, assessment_id: str):
        base_prompt = self.mongo_client.get_prompt_template(prompt_id="68068d260a44ddefa5360a4b")
        follow_up_prompt = self.mongo_client.get_prompt_template(prompt_id="68068d450a44ddefa5360a4c")

        system_prompt = base_prompt["system"] \
            .replace("{job_name}", level_data["job_name"]) \
            .replace("{level}", str(level))

        user_input = str(level_data) + str(job_with_details)
        prompt_template = PromptTemplate(system=system_prompt, user=user_input)
        first_scenario = self.llm_client.generate_scenario_based(course_level=prompt_template)

        # Add ObjectIds to first scenario options
        options_with_ids = []
        for option in first_scenario.options:
            option_data = option.model_dump()
            option_data["option_id"] = ObjectId()
            options_with_ids.append(option_data)

        first_scenario_data = first_scenario.model_dump()
        first_scenario_data["options"] = options_with_ids

        # Update assessment with root scenario
        assessment_doc = self.mongo_client.find_one("assessment", {"_id": ObjectId(assessment_id)})
        if assessment_doc and "assessment" in assessment_doc:
            assessment_questions = assessment_doc["assessment"].get("questions", [])
            assessment_questions.append(first_scenario_data)
            self.mongo_client.update_one(
                collection_name="assessment",
                query={"_id": ObjectId(assessment_id)},
                update={"assessment.questions": assessment_questions}
            )

        # Level 2 generation
        for option in options_with_ids:
            follow_up_system_prompt = follow_up_prompt["system"] \
                .replace("{scenario}", first_scenario_data["scenario_description"]) \
                .replace("{answer_text}", option["option_text"]) \
                .replace("{depth}", str(level + 1))

            follow_up_template = PromptTemplate(system=follow_up_system_prompt, user="")
            follow_up_scenario = self.llm_client.generate_scenario_based(follow_up_template)

            follow_up_options = []
            for follow_option in follow_up_scenario.options:
                data = follow_option.model_dump()
                data["option_id"] = ObjectId()
                follow_up_options.append(data)

            follow_up_doc = follow_up_scenario.model_dump()
            follow_up_doc.update({
                "options": follow_up_options,
                "quiz_id": assessment_id,
                "parent_option_id": option["option_id"]
            })

            second_level_id = self.mongo_client.insert_one("scenario", follow_up_doc)

            # ✅ Level 3 generation
            for second_option in follow_up_options:
                third_prompt = follow_up_prompt["system"] \
                    .replace("{scenario}", follow_up_doc["scenario_description"]) \
                    .replace("{answer_text}", second_option["option_text"]) \
                    .replace("{depth}", str(level + 2))

                third_template = PromptTemplate(system=third_prompt, user="")
                third_scenario = self.llm_client.generate_scenario_based(third_template)

                third_options = []
                for third_option in third_scenario.options:
                    third_data = third_option.model_dump()
                    third_data["option_id"] = ObjectId()
                    third_options.append(third_data)

                third_doc = third_scenario.model_dump()
                third_doc.update({
                    "options": third_options,
                    "quiz_id": assessment_id,
                    "parent_option_id": second_option["option_id"]
                })

                self.mongo_client.insert_one("scenario", third_doc)

    def _get_level_data(self, job: JobDTO, level: int) -> list[dict]:
        level_details = []
        for training in job.trainings:
            try:
                difficulty = training.levels[level].difficulty
                timing = get_train_detail(difficulty)
                level_details.append({
                    "training_name": training.training_name,
                    "training_timing": timing
                })
            except (IndexError, AttributeError):
                continue
        return level_details

    def _generate_details_prompt(self, level_data: dict, level: int, prompt_template: dict) -> PromptTemplate:
        try:
            system = prompt_template["system"] \
                .replace("{job_name}", level_data["job_name"]) \
                .replace("{level}", str(level))
            return PromptTemplate(system=system, user=str(level_data))
        except Exception as e:
            print(e)

    def _generate_assessment_prompt(self, level_data: dict, level: int,
                                    prompt_template: dict, job_with_details: dict) -> PromptTemplate:
        system = prompt_template["system"] \
            .replace("{job_name}", level_data["job_name"]) \
            .replace("{level}", str(level))
        user = str(level_data) + str(job_with_details)
        return PromptTemplate(system=system, user=user)

    def _get_job(self, job_id: str) -> GetJobDTO | None:
        try:
            job_data = self.mongo_client.find_one(collection_name=job_collection, query={"_id": ObjectId(job_id)})
            if not job_data:
                logger.warning(f"Job with ID {job_id} not found.")
                return None
            return GetJobDTO(**job_data)
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {e}")
            return None


# Example usage
if __name__ == "__main__":
    controller = JobDetailsController(mongo_client, llm_client)
    job_id = "68064030a146a64ef0b0d2cd"
    prompt_id = "680656c3950a52dabdb5967f"
    controller.generate_job_detail(job_id, prompt_id)
