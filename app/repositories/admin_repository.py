from app.db.mongodb import db

class AdminRepository:
    def __init__(self):
        self.collection = db.admins

    async def find_by_username(self, username: str):
        return await self.collection.find_one({"username": username})
