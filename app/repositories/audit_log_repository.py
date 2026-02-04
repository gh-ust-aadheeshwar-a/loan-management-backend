from app.db.mongodb import db
from datetime import datetime

class AuditLogRepository:
    def __init__(self):
        self.collection = db.audit_logs

    async def create(self, log: dict):
        await self.collection.insert_one(log)
