from fastapi import APIRouter, Depends, HTTPException
from google.genai import errors
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.config import settings
from app.gemini.rag import client

router = APIRouter(tags=["gemini"])


class Query(BaseModel):
    prompt: str
    model: str = settings.gemini_model


class Answer(BaseModel):
    response: str


@router.post("/ask", response_model=Answer)
def ask_gemini(query: Query, current_user: User = Depends(get_current_user)):
    try:
        result = client.models.generate_content(
            model=query.model,
            contents="give me random sentence in Bulgarian language",
        )
    except errors.APIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return Answer(response=result.text)
