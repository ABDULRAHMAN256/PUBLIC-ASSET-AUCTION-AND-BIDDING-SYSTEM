# models.py — Pydantic schemas for request bodies
from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)
    full_name: str | None = None
    phone: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str
