from app.db.mongodb import db

class AccountRepository:
    def __init__(self):
        self.collection = db.accounts

    async def get_by_user(self, user_id):
        return await self.collection.find_one({"user_id": user_id})

    async def update_balance(self, user_id, amount):
        return await self.collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )
