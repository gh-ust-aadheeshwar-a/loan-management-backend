from app.db.mongodb import db

class ManagerRepository:
    def __init__(self):
        self.collection = db.managers

    async def find_by_manager_id(self, manager_id: str):
        return await self.collection.find_one({"manager_id": manager_id})

    async def create(self, manager_data: dict):
        await self.collection.insert_one(manager_data)
