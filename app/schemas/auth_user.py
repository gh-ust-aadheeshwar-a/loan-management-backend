from pydantic import BaseModel, Field
from typing import Optional

class UserRegisterRequest(BaseModel):
    name: str
    phone: str
    password: str


class UserRegisterResponse(BaseModel):
    user_id: str
    message: str

class UserLoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"



class UserLoginRequest(BaseModel):
    aadhaar: str
    password: Optional[str] = None
    digi_pin: Optional[str] = None
