from datetime import datetime
from typing import Optional
from app.db.mongodb import db
from bson import ObjectId

class UserRepository:
    def __init__(self):
        self.collection = db.users

    async def find_by_phone(self, phone: str):
        return await self.collection.find_one({"phone": phone})

    async def create(self, user_data: dict):
        result = await self.collection.insert_one(user_data)
        return result.inserted_id

    async def find_by_id(self, user_id: str):
        if not ObjectId.is_valid(user_id):
            return None
        return await self.collection.find_one(
            {"_id": ObjectId(user_id)}
        )
    
    async def update_kyc(self, user_id: str, update_data: dict):
    
        return await self.collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    async def update_approval_status(
    self,
    user_id: str,
    approval_status,
    approved_by_manager_id: str,
    remarks: str | None = None
):
         return await self.collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "approval_status": approval_status,
                "approved_by_manager_id": ObjectId(approved_by_manager_id),
                "updated_at": datetime.utcnow()
            }
        }
    )
    async def list_users(
        self,
        approval_status: Optional[str] = None,
        kyc_status: Optional[str] = None
    ):
        query = {}
        if approval_status:
            query["approval_status"] = approval_status
        if kyc_status:
            query["kyc_status"] = kyc_status

        cursor = self.collection.find(query).sort("created_at", -1)
        return cursor


    