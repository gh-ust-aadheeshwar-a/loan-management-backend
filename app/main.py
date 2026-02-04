from fastapi import FastAPI
from app.routers.loan_application import router as loan_router
from app.routers.auth_user import router as auth_user_router
from app.routers.user import router as user_router
from app.routers.bank_manager import router as bank_manager_router
from app.routers.auth_manager import router as manager_auth_router
from app.routers.auth_admin import router as admin_auth_router
from app.routers.admin import router as admin_router
from app.routers.loan_manager import router as loan_manager_router




app = FastAPI(title="Loan Management System")

app.include_router(loan_router)
app.include_router(auth_user_router)
app.include_router(user_router)
app.include_router(bank_manager_router)
app.include_router(manager_auth_router)
app.include_router(admin_auth_router)
app.include_router(admin_router)
app.include_router(loan_manager_router)

