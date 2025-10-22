# app/schema/user_schema.py

from pydantic import BaseModel, EmailStr
from enum import Enum

class Role(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Role | None = None
