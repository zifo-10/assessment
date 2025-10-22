import random
from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from app.constant_manager import CollectionNames
from app.container import mongo_client, llm_client

assessment_router = APIRouter()


class Assessment(BaseModel):
    question_id: str
    selected_answer: str
    time: int


def get_assessment_analysis(user_id: str, training_id: str, assessment: List[Assessment], language: str):
    try:
        user = mongo_client.find_one("users", {"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        training = mongo_client.find_one(CollectionNames.course_collection, {"_id": ObjectId(training_id)})
        if not training:
            raise HTTPException(status_code=404, detail="Training not found")

        training_name = training['name_ar']
        training_name_en = training['name_en']
        training_description = training['description_ar']
        training_description_en = training['description_en']

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
            original_question = mongo_client.find_one(CollectionNames.question_collection,
                                                      {"_id": ObjectId(submitted_question.question_id)})
            if not original_question:
                raise HTTPException(status_code=404, detail="Question not found")

            # Get localized question data
            if language.lower() == "ar":
                question_data = original_question
            else:
                lang_key = f"question_{language.lower()}"
                question_data = original_question.get(lang_key)
                if not question_data:
                    raise HTTPException(status_code=400,
                                        detail=f"Language '{language}' not supported for this question.")

            is_correct = question_data['correct_answer'] == submitted_question.selected_answer
            category = question_data.get("question_category", "uncategorized")

            if category not in category_counts:
                category_counts[category] = {"correct": 0, "incorrect": 0}

            if is_correct:
                correct += 1
                category_counts[category]["correct"] += 1
            else:
                category_counts[category]["incorrect"] += 1

            user_analyses_list.append({
                "question": question_data['question'],
                "user_answer": submitted_question.selected_answer,
                "correct_answer": question_data['correct_answer'],
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
            "student_name": user['name'],
            "correct_answers": correct,
            "incorrect_answers": total_questions - correct,
            "total_questions": total_questions,
            "average_answer_time": average_time,
            "score_percentage": score_percentage,
            "course_title": training_name,
            "course_title_en": training_name_en,
            "course_description": training_description,
            "course_description_en": training_description_en,
            "skill_assessments": [s.dict() for s in skill_assessments],
            "question_progress": question_progress
        }
        return results
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@assessment_router.get("/final_assessment_details/{training_id}/{language}")
def final_assessment_details(training_id: str, language: str):
    try:
        mark = 0
        train = mongo_client.find_one(
            collection_name=CollectionNames.course_collection,
            query={
                "_id": ObjectId(training_id)
            }
        )
        level = train['levels'][0]['difficulty']
        if level == 1:
            mark = 70
        elif level == 2:
            mark = 80
        elif level == 3:
            mark = 90
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
            "question_number": 20,
            "time": 20,
            "pass_mark": mark
        }
        return training_details
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@assessment_router.get("/get_pre_assessment/{training_id}/{language}")
def get_training_details(training_id: str, language: str = 'en'):
    try:
        train = mongo_client.find_one(
            collection_name=CollectionNames.course_collection,
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
                collection_name=CollectionNames.question_collection,
                query={
                    '_id': ObjectId(question_id)
                }
            )
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
            if language == 'ar':
                question['_id'] = str(question['_id'])
                question_list.append({
                    '_id': str(question['_id']),
                    'question': question['question'],
                    'options': question['options'],
                    'correct_answer': question['correct_answer'],
                    'question_type': question['question_type'],
                    'question_category': question['question_category']
                })
            elif language == 'en':
                question_list.append(
                    {
                        '_id': str(question['_id']),
                        'question': question['question_en']['question'],
                        'options': question['question_en']['options'],
                        'correct_answer': question['question_en']['correct_answer'],
                        'question_type': question['question_en']['question_type'],
                        'question_category': question['question_en']['question_category']
                    }
                )
            elif language == 'fr':
                question_list.append(
                    {
                        '_id': str(question['_id']),
                        'question': question['question_fr']['question'],
                        'options': question['question_fr']['options'],
                        'correct_answer': question['question_fr']['correct_answer'],
                        'question_type': question['question_fr']['question_type'],
                        'question_category': question['question_fr']['question_category']
                    }
                )
        return {
            "assessment": question_list
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@assessment_router.post("/submit_pre_assessment/{user_id}/{training_id}")
def submit_pre_assessment(user_id: str, training_id: str, assessment: List[Assessment], language: str = "en"):
    try:
        user = mongo_client.find_one(
            collection_name='users',
            query={"_id": ObjectId(user_id)}
        )
        results = get_assessment_analysis(user_id, training_id, assessment, language)
        results['exam_date'] = datetime.now().strftime("%d-%m")
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


@assessment_router.get("/get_final_assessment/{training_id}/{language}")
def get_final_assessment(training_id: str, language: str):
    try:
        train = mongo_client.find_one(
            collection_name=CollectionNames.course_collection,
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
                collection_name=CollectionNames.question_collection,
                query={
                    '_id': ObjectId(question_id)
                }
            )
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
            if language == 'ar':
                question['_id'] = str(question['_id'])
                question_list.append({
                    '_id': str(question['_id']),
                    'question': question['question'],
                    'options': question['options'],
                    'correct_answer': question['correct_answer'],
                    'question_type': question['question_type'],
                    'question_category': question['question_category']
                })
            elif language == 'en':
                question_list.append(
                    {
                        '_id': str(question['_id']),
                        'question': question['question_en']['question'],
                        'options': question['question_en']['options'],
                        'correct_answer': question['question_en']['correct_answer'],
                        'question_type': question['question_en']['question_type'],
                        'question_category': question['question_en']['question_category']
                    }
                )
            elif language == 'fr':
                question_list.append(
                    {
                        '_id': str(question['_id']),
                        'question': question['question_fr']['question'],
                        'options': question['question_fr']['options'],
                        'correct_answer': question['question_fr']['correct_answer'],
                        'question_type': question['question_fr']['question_type'],
                        'question_category': question['question_fr']['question_category']
                    }
                )
        return {
            "assessment": question_list
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@assessment_router.post("/submit_post_assessment/{user_id}/{training_id}")
def submit_post_assessment(user_id: str, training_id: str, assessment: List[Assessment], language: str):
    try:
        pre_assessment = mongo_client.find_one(collection_name='assessment', query={
            'user_id': user_id,
            'training_id': training_id
        })
        if not pre_assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        pre_assessment = pre_assessment.get("pre_assessment")
        results = get_assessment_analysis(user_id, training_id, assessment, language)
        results['exam_date'] = datetime.now().strftime("%d-%m")
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
        results['pre_assessment_exam_date'] = pre_assessment['exam_date']
        results['pre_assessment_score'] = pre_assessment['score_percentage']
        return results
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
