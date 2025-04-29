import os
from typing import List
from fastapi.responses import JSONResponse
from bson import ObjectId
from pyobjectID import PyObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.client.mongo_client import MongoDBClient
from app.model.assessment_dto import GetAssessmentDTO
from app.model.job_dto import GetJobDTO, TrainingDTO

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

@app.get("/healthcheck")
def healthcheck():
    return JSONResponse(status_code=200, content={"message": "healthy"})


@app.post("/register")
async def register_user(email: str, password: str):
    try:
        insert_user = mongo_client.insert_one(
            collection_name='users',
            document={
                "email": email,
                "password": password
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
                "password": password
            }
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {'user_id': str(user['_id'])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_code}")
async def get_job(job_code: int):
    try:
        job = mongo_client.find_one(
            job_collection,
            query={"job_code": job_code}
        )
        print(job)
        get_train = mongo_client.find(
            'train',
            query={"job_id": ObjectId(job['_id'])}
        )
        training_list = []
        for train in get_train:
            training_list.append(TrainingDTO(**train))
        return training_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
