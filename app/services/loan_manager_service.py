from app.repositories.loan_application_repository import LoanApplicationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.enums.loan import LoanApplicationStatus
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
