from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.ml.member_risk_service import predict_member_financial_risk
from app.routes.sse_utils import stream_db_job
from app.schemas.member_risk import MemberRiskPredictionResponse

router = APIRouter(
    prefix="/member-risk",
    tags=["Member Financial Risk"],
)


@router.get(
    "/project/{project_id}/user/{user_id}",
    response_model=MemberRiskPredictionResponse,
)
def read_member_financial_risk(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    return predict_member_financial_risk(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )


@router.get("/project/{project_id}/user/{user_id}/stream")
async def stream_member_financial_risk(
    project_id: int,
    user_id: int,
):
    return stream_db_job(
        predict_member_financial_risk,
        done_message="Member risk prediction completed.",
        project_id=project_id,
        user_id=user_id,
    )
