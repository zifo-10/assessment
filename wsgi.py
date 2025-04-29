import os
from typing import List

from fastapi.responses import JSONResponse
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
from app.client.mongo_client import MongoDBClient
from pydantic import BaseModel

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
job_collection = os.getenv('COLLECTION_NAME', 'new_job_with_questions')

mongo_client = MongoDBClient(mongo_uri, db_name)


class Assessment(BaseModel):
    question_id: str
    selected_answer: str
    time: int

@app.get("/healthcheck")
def healthcheck():
    return JSONResponse(status_code=200, content={"message": "healthy"})

def get_levels(difficulty):
    levels = {
        1: "Complementary",
        2: "Secondary",
        3: "Mandatory"
    }
    return levels.get(difficulty)


@app.post("/register")
async def register_user(email: str, password: str):
    try:
        insert_user = mongo_client.insert_one(
            collection_name='users',
            document={
                "email": email,
                "password": password,
                "finished_training": [],
            }
        )
        return {'user_id': str(insert_user)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
async def login_user(email: str, password: str):
    try:
        user = mongo_client.find_one(
            collection_name='users',
            query={
                "email": email,
                "password": password,
            }
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {'user_id': str(user['_id'])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job_trainings/{job_code}/{user_id}")
async def get_job(job_code: int, user_id: str):
    try:
        job = mongo_client.find_one(
            job_collection,
            query={"job_code": job_code}
        )

        user = mongo_client.find_one(
            collection_name='users',
            query={"_id": ObjectId(user_id)}
        )

        finished_training_ids = [str(tid) for tid in user.get('finished_training', [])]

        # Use sort key to preserve consistent order (e.g., by training_name or _id)
        get_train = list(mongo_client.find(
            'train',
            query={"job_id": ObjectId(job['_id'])},
            sort=[("training_name", -1)]  # adjust this field as needed
        ))

        training_list = []
        next_opened = False
        last_finished_index = -1

        # Find the index of the last finished training
        for idx, train in enumerate(get_train):
            if str(train['_id']) in finished_training_ids:
                last_finished_index = idx

        for idx, train in enumerate(get_train):
            train_id_str = str(train['_id'])
            level = get_levels(train['level'][0]['difficulty'])

            # Determine status
            if train_id_str in finished_training_ids:
                status = True
            elif idx == last_finished_index + 1:
                status = True
            else:
                status = False

            training_list.append({
                "train_name": train['training_name'],
                "train_level": level,
                "training_id": train_id_str,
                "status": status
            })

        return {
            "training": training_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/training_details/{training_id}")
def get_training_details(training_id: str):
    try:
        train = mongo_client.find_one(
            collection_name='train',
            query={
                "_id": ObjectId(training_id)
            }
        )
        question_number = len(train['question'])
        min = question_number
        training_details = {
            "train_name": train['training_name'],
            "train_description_ar": "",
            "train_description_en": "",
            "question_number": 15,
            "time": 15
        }
        return training_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/get_pre_assessment/{training_id}")
def get_training_details(training_id: str):
    try:
        train = mongo_client.find_one(
            collection_name='train',
            query={
                "_id": ObjectId(training_id)
            }
        )

        questions_ids = train['question']

        # Randomly select up to 20 question IDs
        selected_ids = random.sample(questions_ids, min(20, len(questions_ids)))

        question_list = []

        for question_id in selected_ids:
            question = mongo_client.find_one(
                collection_name='question',
                query={
                    '_id': ObjectId(question_id)
                }
            )
            question['_id'] = str(question['_id'])
            question_list.append(question)
        return {
            "assessment": question_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit_pre_assessment/{user_id}/{training_id}")
def submit_pre_assessment(user_id: str, training_id: str, assessment: List[Assessment]):
    time_taken = 0
    right_answers = 0
    behavior_right = 0
    situational_right = 0
    cognitive_right = 0

    for submitted_question in assessment:
        time_taken += submitted_question.time
        original_question = mongo_client.find_one(
            collection_name='question',
            query={'_id': ObjectId(submitted_question.question_id)}
        )
        if original_question['correct_answer'] == submitted_question.selected_answer:
            right_answers += 1
            if original_question['question_category'] == 'cognitive':
                cognitive_right += 1
            elif original_question['question_category'] == 'situational':
                situational_right += 1
            elif original_question['question_category'] == 'behavior':
                behavior_right += 1

    user_results = {
        "training_id": training_id,
        "right_answers": right_answers,
        "behavior_right": behavior_right,
        "situational_right": situational_right,
        "cognitive_right": cognitive_right,
        "time_taken": time_taken
    }
    user = mongo_client.find_one(
        collection_name='users',
        query={'_id': ObjectId(user_id)}
    )
    user["finished_training"].append(training_id)
    mongo_client.update_one(
        collection_name='users',
        query={'_id': ObjectId(user_id)},
        update={"finished_training": user["finished_training"],}
    )
    return user_results
