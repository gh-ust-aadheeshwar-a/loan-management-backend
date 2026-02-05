from app.repositories.loan_application_repository import LoanApplicationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.enums.loan import LoanApplicationStatus, SystemDecision
from app.schemas.loan_decision import LoanDecision
from datetime import datetime

class LoanManagerService:
    def __init__(self):
        self.loan_repo = LoanApplicationRepository()
        self.audit_repo = AuditLogRepository()

    async def decide_loan(
        self,
        loan_id: str,
        manager_id: str,
        decision: LoanDecision,
        reason: str | None
    ):
        loan = await self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("Loan application not found")
        
        # 🔒 IMPORTANT: enforce system decision rule
        if loan["system_decision"] != SystemDecision.MANUAL_REVIEW:
            raise ValueError(
                "Manual decision only allowed for MANUAL_REVIEW loans"
            )
        if loan["status"] not in [
            LoanApplicationStatus.PENDING,
            LoanApplicationStatus.MANUAL_REVIEW
        ]:
            raise ValueError("Loan already processed")

        if decision == LoanDecision.REJECT and not reason:
            raise ValueError("Rejection reason is mandatory")

        new_status = (
            LoanApplicationStatus.APPROVED
            if decision == LoanDecision.APPROVE
            else LoanApplicationStatus.REJECTED
        )

        await self.loan_repo.update_decision(
            loan_id=loan_id,
            status=new_status,
            decided_by=manager_id,
            reason=reason
        )

        # 🧾 Audit log
        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": f"LOAN_{decision}",
            "entity_type": "LOAN",
            "entity_id": loan_id,
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })

    async def list_loans(self, system_decision=None):
        query = {}
        if system_decision:
            query["system_decision"] = system_decision

        cursor = self.loan_repo.collection.find(query)
        loans = []

        async for loan in cursor:
            loans.append({
                "loan_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "loan_amount": str(loan["loan_amount"]),
                "cibil_score": loan.get("cibil_score"),
                "system_decision": loan.get("system_decision"),
                "status": loan.get("status"),
                "escalated": loan.get("escalated", False)
            })

        return loans
    
    async def confirm_auto_approved(self, loan_id: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)

        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.AUTO_APPROVED:
            raise ValueError("Loan is not auto-approved")

        await self.loan_repo.update_decision(
            loan_id,
            status=LoanApplicationStatus.APPROVED,
            decided_by=manager_id,
            reason=None
        )

    async def confirm_auto_rejected(self, loan_id: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)

        if loan["system_decision"] != SystemDecision.AUTO_REJECTED:
            raise ValueError("Loan not auto-rejected")

        await self.loan_repo.update_decision(
            loan_id,
            status=LoanApplicationStatus.REJECTED,
            decided_by=manager_id,
            reason="Auto rejected by system"
        )
    async def escalate_to_admin(self, loan_id: str, reason: str, manager_id: str):
        loan = await self.loan_repo.find_by_id(loan_id)

        if not loan:
            raise ValueError("Loan not found")

        if loan["system_decision"] != SystemDecision.MANUAL_REVIEW:
            raise ValueError("Only MANUAL_REVIEW loans can be escalated")

        await self.loan_repo.collection.update_one(
            {"_id": loan["_id"]},
            {
                "$set": {
                    "status": "ESCALATED",
                    "escalated": True,
                    "escalated_reason": reason
                }
            }
        )

        await self.audit_repo.create({
            "actor_id": manager_id,
            "actor_role": "LOAN_MANAGER",
            "action": "LOAN_ESCALATED",
            "entity_type": "LOAN",
            "entity_id": loan["_id"],
            "remarks": reason,
            "timestamp": datetime.utcnow()
        })



