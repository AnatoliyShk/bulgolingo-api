from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str  # not EmailStr: it lowercases domains and rejects .local/.test emails Laravel accepted
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
