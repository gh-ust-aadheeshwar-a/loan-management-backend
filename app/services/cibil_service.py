class CIBILService:

    def calculate(self, repayment_summary: dict) -> int:
        score = 700

        if repayment_summary["missed_emis"] == 0:
            score += 50
        else:
            score -= repayment_summary["missed_emis"] * 30

        if repayment_summary["late_payments"] > 2:
            score -= 40

        if repayment_summary["loan_closed_clean"]:
            score += 30

        return max(300, min(score, 900))
