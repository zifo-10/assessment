import os
from typing import Optional

from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.model.llm_dto import PromptTemplate, GeneratedDetails, AssessmentQuiz


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def generate_details(self, course_level: PromptTemplate) -> GeneratedDetails:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[ChatCompletionSystemMessageParam(
                    role="system",
                    content=course_level.system),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=course_level.user
                    )
                ],
                temperature=0,
                response_format=GeneratedDetails
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def generate_assessment(self, course_level: PromptTemplate) -> AssessmentQuiz:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[ChatCompletionSystemMessageParam(
                    role="system",
                    content=course_level.system),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=course_level.user
                    )
                ],
                temperature=0,
                response_format=AssessmentQuiz
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

