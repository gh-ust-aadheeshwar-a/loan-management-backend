from app.enums.loan import SystemDecision
from app.repositories.rule_configuration_repository import (
    RuleConfigurationRepository
)

class CreditRuleService:
    def __init__(self):
        self.repo = RuleConfigurationRepository()

    async def evaluate_cibil(self, cibil_score: int) -> SystemDecision:
        rules = await self.repo.get_active_cibil_rules()

        for rule in rules:
            if rule["min_score"] <= cibil_score <= rule["max_score"]:
                return SystemDecision(rule["decision"])

        # Safety fallback (should never happen)
        return SystemDecision.AUTO_REJECTED
