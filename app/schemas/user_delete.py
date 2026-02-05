from pydantic import BaseModel

class UserDeleteRequest(BaseModel):
    reason: str
