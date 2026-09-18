import json

from google import genai
from google.genai import types

from app.config import settings


class GeminiService:

    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-2.5-flash"

    def generate_exercise(self) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                "Create a random sentence in Bulgarian language with a blank for 1 unknown word "
                "and provide 4 options, with 1 correct option. Also provide an explanation for the "
                "correct answer. Give the response in JSON format with keys: sentence, options, "
                "correct_option, explanation. correct_option is the 0-based index of the correct "
                "option in the options list."
            ),
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text)
