from app.db.mongodb import db

class TransactionRepository:
    def __init__(self):
        self.collection = db.loan_transactions

    async def create(self, txn: dict):
        await self.collection.insert_one(txn)
