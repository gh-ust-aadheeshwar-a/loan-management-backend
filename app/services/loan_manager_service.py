from datetime import datetime, timedelta
from bson import ObjectId
from app.db.mongodb import db
from app.repositories.loan_application_repository import LoanApplicationRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.cibil_service import CIBILService
from app.services.loan_application_service import calculate_emi
from app.enums.loan import LoanApplicationStatus, SystemDecision
from app.schemas.loan_decision import LoanDecision


class LoanManagerService:

    def __init__(self):
        self.loan_app_repo = LoanApplicationRepository()
        self.loan_repo = LoanRepository()  # ACTIVE LOANS
        self.audit_repo = AuditLogRepository()
        self.user_repo = UserRepository()
        self.cibil_service = CIBILService()
    
    
    async def decide_loan(
        self,
        loan_id: str,
        manager_id: str,
        decision: LoanDecision,
        reason: str | None
    ):
        loan = await self.loan_app_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan application not found")

        if loan["system_decision"] != SystemDecision.MANUAL_REVIEW:
            raise ValueError("Only MANUAL_REVIEW loans can be decided manually")

        if decision.name == "REJECT" and not reason:
            raise ValueError("Rejection reason is mandatory")
        
        new_status = (
        LoanApplicationStatus.APPROVED
        if decision.name == "APPROVE"
        else LoanApplicationStatus.REJECTED
        )

        await self.loan_app_repo.collection.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "status": new_status,
                    "decided_by": manager_id,
                    "decision_reason": reason,
                    "decided_at": datetime.utcnow()
                }
            }
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": f"LOAN_{decision.name}",
            "entity_type": "LOAN_APPLICATION",
            "entity_id": loan_id,
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })

    async def confirm_auto_approved(self, loan_id: str, manager_id: str):
        loan = await self.loan_app_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.AUTO_APPROVED:
            raise ValueError("Loan is not auto-approved")

        await self.loan_app_repo.collection.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "status": LoanApplicationStatus.APPROVED,
                    "confirmed_by": manager_id,
                    "confirmed_at": datetime.utcnow()
                }
            }
        )

    async def confirm_auto_rejected(self, loan_id: str, manager_id: str):
        loan = await self.loan_app_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.AUTO_REJECTED:
            raise ValueError("Loan is not auto-rejected")

        await self.loan_app_repo.collection.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "status": LoanApplicationStatus.REJECTED,
                    "confirmed_by": manager_id,
                    "confirmed_at": datetime.utcnow(),
                    "decision_reason": "Auto rejected by system"
                }
            }
        )


    async def escalate_to_admin(self, loan_id: str, reason: str, manager_id: str):
        loan = await self.loan_app_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.MANUAL_REVIEW:
            raise ValueError("Only MANUAL_REVIEW loans can be escalated")

        await self.loan_app_repo.collection.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "status": LoanApplicationStatus.ADMIN_REVIEW,
                    "escalated": True,
                    "escalated_reason": reason,
                    "escalated_by": manager_id,
                    "escalated_at": datetime.utcnow()
                }
            }
        )


    

        # =====================================================
    # LIST ALL LOAN APPLICATIONS (LOAN MANAGER DASHBOARD)
    # =====================================================
    async def list_loans(self, system_decision=None):
        query = {}
        if system_decision:
            query["system_decision"] = system_decision

        cursor = self.loan_app_repo.collection.find(query)

        result = []
        async for loan in cursor:
            result.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": float(loan["loan_amount"].to_decimal()),
                "system_decision": loan.get("system_decision"),
                "status": loan.get("status"),
                "escalated": loan.get("escalated", False),
                "created_at": loan.get("created_at")
            })

        return result


    # =====================================================
    # LIST LOANS READY FOR FINALIZATION (ADMIN_APPROVED)
    # =====================================================
    async def list_loans_ready_for_finalization(self):
        cursor = self.loan_app_repo.collection.find({
            "status": LoanApplicationStatus.ADMIN_APPROVED
        })

        result = []
        async for loan in cursor:
            result.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": float(loan["loan_amount"].to_decimal()),
                "system_decision": loan.get("system_decision"),
                "admin_decision": loan.get("admin_decision"),
                "admin_decision_reason": loan.get("admin_decision_reason"),
                "status": loan["status"]
            })

        return result

    # =====================================================
    # FINALIZE LOAN (AFTER ADMIN APPROVAL)
    # =====================================================
    async def finalize_loan(
        self,
        loan_id: str,
        interest_rate: float,
        tenure_months: int,
        manager_id: str
    ):
        loan_app = await self.loan_app_repo.find_by_id(loan_id)

        if not loan_app:
            raise ValueError("Loan application not found")

        if loan_app["status"] != LoanApplicationStatus.ADMIN_APPROVED:
            raise ValueError("Loan not approved by admin")

        # Convert Decimal128 → float
        principal = float(loan_app["loan_amount"].to_decimal())

        emi_amount = calculate_emi(
            principal,
            tenure_months,
            interest_rate
        )

        # 1️⃣ Create ACTIVE LOAN
        active_loan_id = await self.loan_repo.create({
            "loan_application_id": loan_app["_id"],
            "user_id": loan_app["user_id"],
            "loan_amount": loan_app["loan_amount"],
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
            "emi_amount": emi_amount,
            "status": "ACTIVE",
            "created_at": datetime.utcnow()
        })

        # 2️⃣ Generate EMI schedule
        # ===============================
# EMI SCHEDULE GENERATION
# ===============================
        due_date = datetime.utcnow()   # ✅ datetime, not date

        for i in range(1, tenure_months + 1):
            due_date += timedelta(days=30)

            await db.loan_repayments.insert_one({
                "loan_id": active_loan_id,
                "user_id": loan_app["user_id"],
                "emi_number": i,
                "emi_amount": emi_amount,
                "due_date": due_date,            # ✅ datetime.datetime
                "status": "PENDING",
                "attempts": 0,
                "created_at": datetime.utcnow()
            })


        # 3️⃣ Update LOAN APPLICATION (LOCK IT)
        await self.loan_app_repo.update_by_id(
            loan_id,
            {
                "status": LoanApplicationStatus.FINALIZED,
                "finalized_by": manager_id,
                "finalized_at": datetime.utcnow()
            }
        )

        # 4️⃣ Audit log
        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_FINALIZED",
            "entity_type": "LOAN_APPLICATION",
            "entity_id": loan_id,
            "remarks": f"EMI set to {emi_amount}",
            "timestamp": datetime.utcnow()
        })

        return {
            "message": "Loan finalized successfully",
            "emi_amount": emi_amount
        }

# =====================================================
# LIST ESCALATED LOAN APPLICATIONS (FOR LOAN MANAGER)
# =====================================================
    async def list_escalated_loans(self):
        cursor = self.loan_app_repo.collection.find({
            "escalated": True
        })

        result = []
        async for loan in cursor:
            result.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": float(loan["loan_amount"].to_decimal()),
                "system_decision": loan.get("system_decision"),
                "escalated_reason": loan.get("escalated_reason"),
                "escalated_at": loan.get("escalated_at"),
                "status": loan.get("status")
            })

        return result
    async def list_finalized_loans(self):
        cursor = self.loan_app_repo.collection.find({
            "status": LoanApplicationStatus.FINALIZED
        })

        result = []
        async for loan in cursor:
            result.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": float(loan["loan_amount"].to_decimal()),
                "finalized_at": loan.get("finalized_at"),
                "finalized_by": loan.get("finalized_by")
            })

        return result
