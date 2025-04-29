import os
from typing import Optional

from openai import OpenAI

from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.constant import user_analyses_prompt
from app.model.llm_response import PromptTemplate, GeneratedDetails, AssessmentQuiz, ScenarioQuestion, AnalysisResult


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

    def generate_scenario_based(self, course_level: PromptTemplate) -> ScenarioQuestion:
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
                response_format=ScenarioQuestion
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def analyses_user(self, user_answers: list, language: str = 'en'):
        try:
            print(language)
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[ChatCompletionSystemMessageParam(
                    role="system",
                    content=user_analyses_prompt.replace("{lang}", language)),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(user_answers) + f"\nAnswer in {language} language:"
                    )
                ],
                temperature=0,
                response_format=AnalysisResult
            )
            return response.choices[0].message.parsed.feedback
        except Exception as e:
            raise e


