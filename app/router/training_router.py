from bson import ObjectId
from fastapi import HTTPException, APIRouter

from app.constant_manager import CollectionNames
from app.container import mongo_client

training_router = APIRouter()


@training_router.get("/training_details/{training_id}/{language}")
def get_training_details(training_id: str, language: str):
    try:
        train = mongo_client.find_one(
            collection_name=CollectionNames.course_collection,
            query={
                "_id": ObjectId(training_id)
            }
        )
        if not train:
            raise HTTPException(status_code=404, detail="Training not found")
        if language == 'en':
            training_name = train['name_en']
            train_description = train['description_en']
        else:
            training_name = train['name_ar']
            train_description = train['description_ar']
        training_details = {
            "train_name": training_name,
            "train_description": train_description,
            "question_number": 15,
            "time": 15,
        }
        return training_details
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
