from bson import ObjectId
from fastapi import HTTPException, APIRouter, Depends

from app.auth.dependencies import role_required
from app.container import mongo_client

user_router = APIRouter()


@user_router.post("/user/{user_id}")
async def get_user_by_id(user_id: str,
                         current_user=Depends(role_required(["admin", "super_admin", "user"]))):
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
