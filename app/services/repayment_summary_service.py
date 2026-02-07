from app.db.mongodb import db
from bson import ObjectId

class RepaymentSummaryService:

    async def build_summary(self, loan_id: ObjectId):
        total_emis = await db.loan_repayments.count_documents(
            {"loan_id": loan_id}
        )

        paid_emis = await db.loan_repayments.count_documents(
            {"loan_id": loan_id, "status": "PAID"}
        )

        missed_emis = await db.loan_repayments.count_documents(
            {"loan_id": loan_id, "status": "FAILED"}
        )

        late_payments = await db.loan_transactions.count_documents({
            "loan_id": loan_id,
            "transaction_type": "PENALTY",
            "status": "PAID"
        })

        return {
            "total_emis": total_emis,
            "paid_emis": paid_emis,
            "missed_emis": missed_emis,
            "late_payments": late_payments,
            "loan_closed_clean": missed_emis == 0
        }
