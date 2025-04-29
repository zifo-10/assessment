import os
import random
from datetime import datetime
from typing import List

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.client.llm_client import OpenAIClient
from app.client.mongo_client import MongoDBClient

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
llm_client = OpenAIClient()
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


def get_assessment_analysis(user_id: str, training_id: str, assessment: List[Assessment], language: str = "Arabic"):
    user = mongo_client.find_one("users", {"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    training = mongo_client.find_one("train", {"_id": ObjectId(training_id)})
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")

    training_name = training.get("training_name", "") if language == "en" else training.get("training_name_ar", "")
    training_description = training.get("training_description", "") if language == "en" else training.get(
        "training_description_ar", "")

    total_time = 0
    correct = 0
    user_analyses_list = []
    category_counts = {
        "cognitive": {"correct": 0, "incorrect": 0},
        "behavior": {"correct": 0, "incorrect": 0},
        "situational": {"correct": 0, "incorrect": 0}
    }

    for submitted_question in assessment:
        total_time += submitted_question.time
        original_question = mongo_client.find_one("question", {"_id": ObjectId(submitted_question.question_id)})
        if not original_question:
            raise HTTPException(status_code=404, detail="Question not found")

        is_correct = original_question['correct_answer'] == submitted_question.selected_answer
        category = original_question.get("question_category", "uncategorized")

        if category not in category_counts:
            category_counts[category] = {"correct": 0, "incorrect": 0}

        if is_correct:
            correct += 1
            category_counts[category]["correct"] += 1
        else:
            category_counts[category]["incorrect"] += 1

        user_analyses_list.append({
            "question": original_question['question'],
            "user_answer": submitted_question.selected_answer,
            "correct_answer": original_question['correct_answer'],
            "question_category": category,
        })

    total_questions = len(assessment)
    average_time = int(total_time / total_questions) if total_questions > 0 else 0

    skill_assessments = llm_client.analyses_user(user_analyses_list, language)

    question_progress = [
        {
            "category": category,
            "correct": counts["correct"],
            "incorrect": counts["incorrect"],
            "total": counts["correct"] + counts["incorrect"]
        }
        for category, counts in category_counts.items()
    ]
    score_percentage = round((correct / total_questions) * 100, 2) if total_questions > 0 else 0.0
    results = {
        "submitted_at": datetime.now(),
        "correct_answers": correct,
        "incorrect_answers": total_questions - correct,
        "total_questions": total_questions,
        "average_answer_time": average_time,
        "score_percentage": score_percentage,  # ✅ Add this line
        "course_title": training_name,
        "course_description": training_description,
        "skill_assessments": [s.dict() for s in skill_assessments],
        "question_progress": question_progress
    }
    return results


@app.post("/register")
async def register_user(email: str, password: str, name: str):
    try:
        user_existed = mongo_client.find_one("users", {"email": email})
        if user_existed:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        insert_user = mongo_client.insert_one(
            collection_name='users',
            document={
                "name": name,
                "email": email,
                "password": password,
                "finished_training": [],
            }
        )
        return {'user_id': str(insert_user)}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
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
        user['_id'] = str(user['_id'])
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/{user_id}")
async def get_user_by_id(user_id: str):
    try:
        user = mongo_client.find_one(collection_name='users', query={"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user['_id'] = str(user['_id'])
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job_trainings/{job_code}/{user_id}")
async def get_job(job_code: int, user_id: str):
    try:
        job = mongo_client.find_one(
            job_collection,
            query={"job_code": job_code}
        )
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        user = mongo_client.find_one(
            collection_name='users',
            query={"_id": ObjectId(user_id)}
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        finished_training_ids = [str(tid) for tid in user.get('finished_training', [])]

        # Use sort key to preserve consistent order (e.g., by training_name or _id)
        get_train = list(mongo_client.find(
            'train',
            query={"job_id": ObjectId(job['_id'])},
            sort=[("training_name", -1)]  # adjust this field as needed
        ))
        if not get_train:
            raise HTTPException(status_code=404, detail="No training found")

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
    except HTTPException as e:
        raise e
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
        if not train:
            raise HTTPException(status_code=404, detail="Training not found")

        question_number = len(train['question'])

        training_details = {
            "train_name": train['training_name'],
            "train_description_ar": "",
            "train_description_en": "",
            "question_number": 15,
            "time": 15,
        }
        return training_details
    except HTTPException as e:
        raise e
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
        if not train:
            raise HTTPException(status_code=404, detail="Training not found")

        questions_ids = train['question']

        # Randomly select up to 20 question IDs
        selected_ids = random.sample(questions_ids, min(15, len(questions_ids)))

        question_list = []

        for question_id in selected_ids:
            question = mongo_client.find_one(
                collection_name='question',
                query={
                    '_id': ObjectId(question_id)
                }
            )
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
            question['_id'] = str(question['_id'])
            question_list.append(question)
        return {
            "assessment": question_list
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit_pre_assessment/{user_id}/{training_id}")
def submit_pre_assessment(user_id: str, training_id: str, assessment: List[Assessment], language: str = "Arabic"):
    try:
        user = mongo_client.find_one(
            collection_name='users',
            query={"_id": ObjectId(user_id)}
        )
        results = get_assessment_analysis(user_id, training_id, assessment, language)
        finished_training = user["finished_training"]
        finished_training.append(training_id)
        mongo_client.update_one(
            collection_name="users",
            query={"_id": ObjectId(user_id)},
            update={
                "finished_training": finished_training,
            }
        )
        mongo_client.insert_one(
            collection_name="assessment",
            document={
                "user_id": user_id,
                "training_id": training_id,
                "pre_assessment": results
            }
        )
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_final_assessment/{training_id}")
def get_final_assessment(training_id: str):
    try:
        train = mongo_client.find_one(
            collection_name='train',
            query={
                "_id": ObjectId(training_id)
            }
        )
        if not train:
            raise HTTPException(status_code=404, detail="Training not found")

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
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
            question['_id'] = str(question['_id'])
            question_list.append(question)
        return {
            "assessment": question_list
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit_post_assessment/{user_id}/{training_id}")
def submit_post_assessment(user_id: str, training_id: str, assessment: List[Assessment], language: str = "Arabic"):
    try:
        results = get_assessment_analysis(user_id, training_id, assessment, language)
        mongo_client.update_one(
            collection_name="assessment",
            query={
                'user_id': user_id,
                'training_id': training_id
            },
            update={
                "post_assessment": results
            }
        )
        return results
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
