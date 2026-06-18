from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import errors
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["gemini"])

client = genai.Client(api_key=settings.gemini_api_key)


class Query(BaseModel):
    prompt: str
    model: str = "gemini-2.5-flash"


class Answer(BaseModel):
    response: str


@router.post("/ask", response_model=Answer)
def ask_gemini(query: Query):
    try:
        result = client.models.generate_content(
            model=query.model,
            contents="give me random sentence in Bulgarian language",
        )
    except errors.APIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return Answer(response=result.text)
