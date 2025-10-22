from bson import ObjectId
from fastapi import HTTPException, APIRouter

from app.constant_manager import CollectionNames
from app.container import mongo_client

dashboard_router = APIRouter()



@dashboard_router.post("/dashboard/{user_id}")
def dashboard(user_id: str):
    try:
        user = mongo_client.find_one(
            collection_name='users',
            query={"_id": ObjectId(user_id)}
        )
        training_names = []
        finished_training = user.get('finished_training')
        if not finished_training:
            raise HTTPException(status_code=404, detail="Finished training not found")
        for id in finished_training:
            train = mongo_client.find_one(
                collection_name=CollectionNames.course_collection,
                query={
                    '_id': ObjectId(id)
                }
            )
            if not train:
                raise HTTPException(status_code=404, detail="This use have not finihsed any train yet")
            training_names.append(train['name_ar'])

        assessments = mongo_client.find(collection_name='assessment', query={
            'user_id': user_id,
        })
        courses_assessment_data = []
        for assessment in assessments:
            train_name = assessment['pre_assessment']['course_title']
            train_pre_assessment_score = assessment['pre_assessment']['score_percentage']
            pre_assessment_avg_time = assessment['pre_assessment']['average_answer_time']
            train_post_assessment_score = assessment['post_assessment']['score_percentage']
            post_assessment_avg_time = assessment['post_assessment']['average_answer_time']
            train = {
                'training_name': train_name,
                'pre_assessment_score': train_pre_assessment_score,
                'pre_assessment_avg_time': pre_assessment_avg_time,
                'post_assessment_score': train_post_assessment_score,
                'post_assessment_avg_time': post_assessment_avg_time,
            }
            courses_assessment_data.append(train)

        dashboard = {
            "student_name": user['name'],
            "courses_completed": len(user['finished_training']),
            "courses_assessment": courses_assessment_data
        }
        # mongo_client.update_one(
        #     collection_name="assessment",
        #     query={
        #         'user_id': user_id,
        #         'training_id': training_id
        #     },
        #     update={
        #         'dashboard': dashboard
        #     }
        # )
        return dashboard

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
