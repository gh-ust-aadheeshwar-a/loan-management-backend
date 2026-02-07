from datetime import datetime
from bson import ObjectId
from app.repositories.account_repository import AccountRepository

class AccountService:
    def __init__(self):
        self.repo = AccountRepository()

    async def deposit(self, user_id: str, amount: float):
        if amount <= 0:
            raise ValueError("Invalid amount")

        await self.repo.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$inc": {"balance": amount},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )
