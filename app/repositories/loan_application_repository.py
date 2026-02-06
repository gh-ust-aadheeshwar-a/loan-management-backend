from datetime import datetime
from app.db.mongodb import db
from app.models.loan_application import LoanApplication
from bson import ObjectId
from app.enums.loan import LoanApplicationStatus


class LoanApplicationRepository:
    def __init__(self):
        self.collection = db.loan_applications

    async def find_by_idempotency_key(self,key: str):
        return await self.collection.find_one({"idempotency_key": key})
    
    async def create(self,data: dict):
        result = await self.collection.insert_one(data)
        return result.inserted_id
    
    async def find_by_id(self, loan_id: str):
        if not ObjectId.is_valid(loan_id):
            return None
        return await self.collection.find_one(
            {"_id": ObjectId(loan_id)}
        )
    async def update_decision(
        self,
        loan_id: str,
        status,
        decided_by: str,
        reason: str | None
    ):
        return await self.collection.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "status": status,
                    "decision_reason": reason,
                    "decided_by": ObjectId(decided_by),
                    "decided_at": datetime.utcnow()
                }
            }
        )
    async def count_active_loans(self, user_id: str) -> int:
        return await self.collection.count_documents({
            "user_id": ObjectId(user_id),
            "status": {
                "$in": [
                    LoanApplicationStatus.APPROVED,
                    LoanApplicationStatus.MANUAL_REVIEW,
                    LoanApplicationStatus.PENDING
                ]
            }
        })
    async def find_escalated_loans(self):
        cursor = self.collection.find({
            "status": "ESCALATED",
            "escalated": True
        }).sort("applied_at", -1)
        return cursor
