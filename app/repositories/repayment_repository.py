from app.db.mongodb import db

class RepaymentRepository:
    def __init__(self):
        self.collection = db.loan_repayments

    async def get_due_emis(self, today):
        return self.collection.find({
            "due_date": {"$lte": today},
            "status": {"$in": ["PENDING", "FAILED"]}
        })
