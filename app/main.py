from fastapi import FastAPI

from app.routers.auth_admin import router as auth_admin_router
from app.routers.auth_manager import router as auth_manager_router
from app.routers.auth_user import router as auth_user_router

from app.routers.admin import router as admin_router
from app.routers.bank_manager import router as bank_manager_router
from app.routers.loan_manager import router as loan_manager_router
from app.routers.user import router as user_router
from app.routers.loan_application import router as loan_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler.emi_scheduler import process_due_emis

app = FastAPI(
    title="Loan Management System",
    description="""
## 🔐 Authentication & Authorization

This application uses **JWT-based authentication** with **Role-Based Access Control (RBAC)**.

### Login Endpoints
Use the appropriate login endpoint based on your role:

- **Admin Login** → `/auth/admin/login`
- **Manager Login** → `/auth/manager/login`
- **User Login** → `/auth/user/login`

Each login endpoint returns a **JWT access token** containing the user role.

### How to use Swagger
1. Call a login endpoint
2. Copy the `access_token`
3. Click **Authorize 🔐**
4. Paste: `Bearer <access_token>`
5. Call protected APIs

### Role Enforcement
Access to APIs is enforced using the **role claim inside the JWT**, not by the login endpoint.
""",
    version="1.0.0"
)
scheduler = AsyncIOScheduler()
scheduler.add_job(process_due_emis, "cron", hour=2)
scheduler.start()
# =========================
# AUTH ROUTERS
# =========================
app.include_router(auth_admin_router)
app.include_router(auth_manager_router)
app.include_router(auth_user_router)

# =========================
# BUSINESS ROUTERS
# =========================
app.include_router(admin_router)
app.include_router(bank_manager_router)
app.include_router(loan_manager_router)
app.include_router(user_router)
app.include_router(loan_router)
