from enum import Enum

class TransactionType(str, Enum):
    EMI = "EMI"
    PENALTY = "PENALTY"
    REFUND = "REFUND"

class TransactionStatus(str, Enum):
    PAID = "PAID"
    FAILED = "FAILED"
    PENDING = "PENDING"
