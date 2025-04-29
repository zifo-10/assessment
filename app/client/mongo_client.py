from bson import ObjectId
from pymongo import MongoClient, errors
from typing import Any, Dict, List, Optional


class MongoDBClient:
    def __init__(self, uri: str, db_name: str):
        """
        Initialize MongoDB client and database.
        """
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        try:
            result = self.db[collection_name].insert_one(document)
            return str(result.inserted_id)
        except errors.PyMongoError as e:
            print(f"Error inserting document into '{collection_name}': {e}")
            return None

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        try:
            result = self.db[collection_name].insert_many(documents)
            return [str(inserted_id) for inserted_id in result.inserted_ids]
        except errors.PyMongoError as e:
            print(f"Error inserting documents into '{collection_name}': {e}")
            return []

    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return self.db[collection_name].find_one(query)
        except errors.PyMongoError as e:
            print(f"Error finding document in '{collection_name}': {e}")
            return None

    def find(
            self,
            collection_name: str,
            query: Dict[str, Any],
            projection: Optional[Dict[str, int]] = None,
            limit: Optional[int] = 100,
            skip: Optional[int] = 0,
            sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[collection_name].find(query, projection).skip(skip).limit(limit)
            if sort:
                cursor = cursor.sort(sort)
            return list(cursor)
        except errors.PyMongoError as e:
            print(f"Error finding documents in '{collection_name}': {e}")
            return []

    def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        try:
            result = self.db[collection_name].update_one(query, {"$set": update})
            return result.modified_count > 0
        except errors.PyMongoError as e:
            print(f"Error updating document in '{collection_name}': {e}")
            return False

    def update_many(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        try:
            result = self.db[collection_name].update_many(query, {"$set": update})
            return result.modified_count > 0
        except errors.PyMongoError as e:
            print(f"Error updating documents in '{collection_name}': {e}")
            return False

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        try:
            result = self.db[collection_name].delete_one(query)
            return result.deleted_count > 0
        except errors.PyMongoError as e:
            print(f"Error deleting document from '{collection_name}': {e}")
            return False

    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> bool:
        try:
            result = self.db[collection_name].delete_many(query)
            return result.deleted_count > 0
        except errors.PyMongoError as e:
            print(f"Error deleting documents from '{collection_name}': {e}")
            return False

    def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            return list(self.db[collection_name].aggregate(pipeline))
        except errors.PyMongoError as e:
            print(f"Error aggregating documents in '{collection_name}': {e}")
            return []

    def get_prompt_template(self, prompt_id: str, collection_name: str = "prompt") -> Optional[Dict[str, Any]]:
        try:
            return self.db[collection_name].find_one({"_id": ObjectId(prompt_id)})
        except errors.PyMongoError as e:
            print(f"Error getting prompt template from '{collection_name}': {e}")
            return None
