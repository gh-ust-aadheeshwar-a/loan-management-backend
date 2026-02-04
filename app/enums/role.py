from enum import Enum

class Role(str, Enum):
    USER = "USER"
    BANK_MANAGER = "BANK_MANAGER"
    LOAN_MANAGER = "LOAN_MANAGER"
    ADMIN = "ADMIN"
