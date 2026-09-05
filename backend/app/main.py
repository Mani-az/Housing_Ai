import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.database.database import engine
from app.database.base import Base

from app.models import (
    user,
    project,
    payment,
    expense,
    risk_data,
    property_listing,
    economic_indicator,
    project_participant,
    project_owner,
    auth_account,
    payment_plan,
    membership_request,
)

from app.routes.user_routes import router as user_router
from app.routes.property_routes import router as property_router
from app.routes.project_routes import router as project_router
from app.routes.project_participant_routes import router as participant_router
from app.routes.economic_indicator_routes import router as economic_indicator_router
from app.routes.ml_routes import router as ml_router
from app.routes.payment_routes import router as payment_router
from app.routes.member_risk_routes import router as member_risk_router
from app.routes.project_delay_routes import router as project_delay_router
from app.routes.project_owner_routes import router as project_owner_router
from app.routes.membership_request_routes import router as membership_request_router
from app.routes.valuation_routes import router as valuation_router


logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

# `create_all` does not add columns to an already-created demo database. Keep
# the small MembershipRequest risk payload migration self-contained so an
# earlier coursework database can still boot after the Member-panel update.
try:
    if engine.dialect.name == "mssql":
        with engine.begin() as connection:
            connection.execute(text("IF COL_LENGTH('membership_requests', 'risk_details') IS NULL ALTER TABLE membership_requests ADD risk_details NVARCHAR(MAX) NULL"))
except Exception:
    logger.exception("Could not add membership_requests.risk_details during startup.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "AI-Powered Cooperative Housing Finance System API is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


app.include_router(user_router)
app.include_router(property_router)
app.include_router(project_router)
app.include_router(economic_indicator_router)
app.include_router(ml_router)
app.include_router(participant_router)
app.include_router(payment_router)
app.include_router(member_risk_router)
app.include_router(project_delay_router)
app.include_router(project_owner_router)
app.include_router(membership_request_router)
app.include_router(valuation_router)
