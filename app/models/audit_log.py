from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.utils.object_id import PyObjectId


class AuditLog(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    actor_id: PyObjectId
    actor_role: str
    action: str
    entity_type: str
    entity_id: PyObjectId
    remarks: str
    timestamp: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
