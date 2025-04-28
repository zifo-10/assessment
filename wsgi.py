import os
from typing import List

from pyobjectID import PyObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.client.mongo_client import MongoDBClient
from app.model.assessment_dto import GetAssessmentDTO
from app.model.job_dto import GetJobDTO

app = FastAPI()


load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME', 'assessment')
job_collection = os.getenv('COLLECTION_NAME', 'new_job')
assessment_collection = 'assessment'
scenario_collection = 'scenario'

mongo_client = MongoDBClient(mongo_uri, db_name)


@app.get("/job", response_model=List[GetJobDTO])
async def list_jobs(limit: int = Query(10, ge=1), skip: int = Query(0, ge=0)):
    try:
        job_list = []
        # Pass the limit and skip to the find method
        jobs = mongo_client.find(
            job_collection,
            {},
            limit=limit,
            skip=skip
        )

        for job in jobs:
            job_list.append(GetJobDTO(**job))

        return job_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job_id/{job_id}/{level}")
async def get_assessment(job_id: str,
                        level: int):
    try:
        quiz = mongo_client.find_one(
            assessment_collection,
            {"job_id": job_id,
                "level": level}
        )
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        # Convert ObjectId to string for JSON serialization
        quiz = GetAssessmentDTO(**quiz)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessment/{item_id}")
async def get_assessment_with_scenario(item_id: PyObjectId):
    # Step 1: Convert the item_id to ObjectId
    # Step 2: Get the assessment document
    assessment_pipeline = [{"$match": {"_id": item_id}}]
    assessment_docs = mongo_client.aggregate(assessment_collection, assessment_pipeline)

    if not assessment_docs:
        raise HTTPException(status_code=404, detail="Assessment not found")

    assessment_doc = assessment_docs[0]

    # Step 3: Extract first valid option_id from any question
    try:
        first_option_id = None
        questions = assessment_doc.get("assessment", {}).get("questions", [])
        scenario_q = questions[-1]
        options = scenario_q["options"]
        options_id_list = []
        for i in options:
            i["option_id"] = str(i["option_id"])
            options_id_list.append(i)
        scenario_q["options"] = options_id_list

        return scenario_q
    except Exception as e:
        raise e


@app.get("/scenario-base-q/{item_id}")
async def get_scenario_base_question(item_id: PyObjectId):
    try:
        scenario_base = mongo_client.find_one(
            scenario_collection,
            {"parent_option_id": item_id}
        )

        if not scenario_base:
            raise HTTPException(status_code=404, detail="Scenario not found")

        for option in scenario_base.get("options", []):
            option["option_id"] = str(option["option_id"])

        scenario_base["parent_option_id"] = str(scenario_base["parent_option_id"])
        scenario_base["_id"] = str(scenario_base["_id"])

        return scenario_base
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prompt")
async def list_prompt(limit: int = Query(10, ge=1), skip: int = Query(0, ge=0)):
    try:
        prompt_list = []
        # Pass the limit and skip to the find method
        prompts = mongo_client.find(
            "prompt",
            {},
            limit=limit,
            skip=skip
        )

        for prompt in prompts:
            prompt['_id'] = str(prompt['_id'])
            prompt_list.append(prompt)

        return prompt_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
