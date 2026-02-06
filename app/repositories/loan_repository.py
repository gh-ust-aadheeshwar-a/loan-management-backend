from app.db.mongodb import db

class LoanRepository:
    def __init__(self):
        self.collection = db.loans

    async def create(self, loan_doc: dict):
        result = await self.collection.insert_one(loan_doc)
        return result.inserted_id
