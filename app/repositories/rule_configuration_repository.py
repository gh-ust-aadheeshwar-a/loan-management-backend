from app.db.mongodb import db

class RuleConfigurationRepository:
    def __init__(self):
        self.collection = db.rule_configurations

    async def get_active_cibil_rules(self):
        cursor = self.collection.find(
            {"rule_type": "CIBIL_SCORE", "active": True}
        ).sort("min_score", -1)

        return await cursor.to_list(length=None)
