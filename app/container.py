from app.client.llm_client import OpenAIClient
from app.client.mongo_client import MongoDBClient
from app.config import settings



mongo_uri = settings.MONGO_URI
db_name = settings.DB_NAME


def get_mongo_client() -> MongoDBClient:
    return MongoDBClient(mongo_uri, db_name)

mongo_client = get_mongo_client()

def get_llm_client() -> OpenAIClient:
    return OpenAIClient(api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini")

llm_client = get_llm_client()