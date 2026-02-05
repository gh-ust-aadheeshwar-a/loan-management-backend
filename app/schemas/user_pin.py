from pydantic import BaseModel, Field

class DigiPinRequest(BaseModel):
    digi_pin: str = Field(..., min_length=4, max_length=6)
