from pydantic import BaseModel, HttpUrl

class IncomeDetails(BaseModel):
    declared_monthly_income: float
    income_slip_url: HttpUrl

    class Config:
        frozen = True
