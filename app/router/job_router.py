from bson import ObjectId
from fastapi import HTTPException, APIRouter, Depends

from app.auth.dependencies import role_required
from app.constant_manager import CollectionNames
from app.container import mongo_client

job_router = APIRouter()


def get_levels(difficulty):
    levels = {
        1: "Complementary",
        2: "Secondary",
        3: "Mandatory"
    }
    return levels.get(difficulty)


@job_router.get('')
async def get_all_jobs(page: int = 1,
                       limit: int = 10):
    try:
        skip = (page - 1) * limit
        jobs_cursor = mongo_client.find(
            collection_name=CollectionNames.job_collection,
            query={},
            skip=skip,
            limit=limit
        )
        jobs = list(jobs_cursor)
        for job in jobs:
            job['_id'] = str(job['_id'])
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@job_router.get("/job_trainings/{job_code}/{user_id}/{language}")
async def get_job(job_code: int,
                  user_id: str,
                  language: str,
                  current_user = Depends(role_required(["admin", "super_admin", "user"]))):
    try:
        job = mongo_client.find_one(
            CollectionNames.job_collection,
            query={"job_code": job_code}
        )
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job_name = job['job_name']
        user = mongo_client.find_one(
            collection_name='users',
            query={"_id": ObjectId(user_id)}
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        finished_training_ids = [str(tid) for tid in user.get('finished_training', [])]

        # Use sort key to preserve consistent order (e.g., by training_name or _id)
        get_train = list(mongo_client.aggregate(
            CollectionNames.course_collection,
            pipeline=[
                {"$match": {"job_id": ObjectId(job['_id'])}},
                {"$addFields": {
                    "max_difficulty": {"$max": "$levels.difficulty"}
                }},
                {"$sort": {"max_difficulty": -1}}
            ]
        ))
        if not get_train:
            raise HTTPException(status_code=404, detail="No training found")

        training_list = []
        next_opened = False
        last_finished_index = -1

        opened_assigned = False

        for train in get_train:
            train_id_str = str(train['_id'])
            level = get_levels(train['levels'][0]['difficulty'])

            if train_id_str in finished_training_ids:
                status = True
            elif not opened_assigned:
                status = True
                opened_assigned = True
            else:
                status = False

            if language == 'en':
                job_name = job['job_name_en']
                training_name = train['name_en']
                train_description = train['description_en']
            else:
                training_name = train['name_ar']
                train_description = train['description_ar']

            training_list.append({
                "train_name": training_name,
                "train_description": train_description,
                "train_level": level,
                "training_id": train_id_str,
                "status": status
            })

        return {
            "job_name": job_name,
            "training": training_list
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
