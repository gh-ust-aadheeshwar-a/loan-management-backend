from datetime import datetime
import uuid

from app.db.mongodb import db
from app.services.cibil_service import CIBILService
from app.services.repayment_summary_service import RepaymentSummaryService

cibil_service = CIBILService()
summary_service = RepaymentSummaryService()


async def process_due_emis():
    """
    Auto-debit EMI scheduler
    Runs via APScheduler / cron
    """

    now = datetime.utcnow()

    # 🔍 Find all due & unpaid EMIs
    cursor = db.loan_repayments.find({
        "due_date": {"$lte": now},
        "status": {"$in": ["PENDING", "FAILED"]}
    })

    async for emi in cursor:

        # 🧱 HARD IDEMPOTENCY GUARD
        if emi["status"] == "PAID":
            continue

        # 🔎 Fetch user account
        account = await db.accounts.find_one({
            "user_id": emi["user_id"]
        })

        # =====================================================
        # ❌ INSUFFICIENT BALANCE
        # =====================================================
        if not account or account["balance"] < emi["emi_amount"]:

            await db.loan_repayments.update_one(
                {"_id": emi["_id"]},
                {
                    "$set": {
                        "status": "FAILED",
                        "updated_at": now
                    },
                    "$inc": {
                        "attempts": 1
                    }
                }
            )

            # 📉 Update loan-level missed EMI count
            await db.loans.update_one(
                {"_id": emi["loan_id"]},
                {
                    "$inc": {
                        "missed_emis": 1
                    }
                }
            )

            # 📊 Recalculate CIBIL
            summary = await summary_service.build_summary(
                emi["loan_id"]
            )
            new_cibil = cibil_service.calculate(summary)

            await db.users.update_one(
                {"_id": emi["user_id"]},
                {
                    "$set": {
                        "cibil_score": new_cibil,
                        "cibil_updated_at": now
                    }
                }
            )

            continue

        # =====================================================
        # ✅ SUFFICIENT BALANCE → DEBIT EMI
        # =====================================================
        new_balance = account["balance"] - emi["emi_amount"]

        # 💳 Debit account
        await db.accounts.update_one(
            {"_id": account["_id"]},
            {
                "$set": {
                    "balance": new_balance,
                    "updated_at": now
                }
            }
        )

        # ✅ Mark EMI as paid
        await db.loan_repayments.update_one(
            {"_id": emi["_id"]},
            {
                "$set": {
                    "status": "PAID",
                    "paid_at": now,
                    "updated_at": now
                }
            }
        )

        # 🧾 Transaction history
        await db.loan_transactions.insert_one({
            "transaction_id": f"TXN-{uuid.uuid4()}",
            "loan_id": emi["loan_id"],
            "user_id": emi["user_id"],
            "emi_number": emi["emi_number"],
            "amount": emi["emi_amount"],
            "transaction_type": "EMI",
            "status": "PAID",
            "balance_after": new_balance,
            "created_at": now
        })

        # 📊 Update loan stats
        await db.loans.update_one(
            {"_id": emi["loan_id"]},
            {
                "$inc": {
                    "paid_emis": 1
                }
            }
        )

        # 📈 Recalculate CIBIL after successful EMI
        summary = await summary_service.build_summary(
            emi["loan_id"]
        )
        new_cibil = cibil_service.calculate(summary)

        await db.users.update_one(
            {"_id": emi["user_id"]},
            {
                "$set": {
                    "cibil_score": new_cibil,
                    "cibil_updated_at": now
                }
            }
        )
