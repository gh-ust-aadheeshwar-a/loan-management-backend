from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.utils.object_id import PyObjectId

class Account(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    balance: float
    status: str = "ACTIVE"
    created_at: datetime
    updated_at: datetime
