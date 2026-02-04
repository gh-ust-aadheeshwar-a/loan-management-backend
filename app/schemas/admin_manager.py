from pydantic import BaseModel
from app.enums.role import Role

class CreateManagerRequest(BaseModel):
    manager_id: str
    name: str
    phone: str
    role: Role
    password: str


class CreateManagerResponse(BaseModel):
    manager_id: str
    role: Role
    message: str
