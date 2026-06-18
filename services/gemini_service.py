from django.conf import settings
from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import errors
from pydantic import BaseModel

from app.config import settings

class GeminiService:

    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-2.5-flash"
        self.router = APIRouter(tags=["gemini"])

    def generate_exercise(self) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": f"Create random sentence in Bulgarian language with a blank for the 1 unknown word and provide 4 options, with 1 correct option. Also provide an explanation for the correct answer. Give response in JSON format with keys: sentence, options, correct_option, explanation. Options keys are numeric"}
            ]
        )
        return response.text