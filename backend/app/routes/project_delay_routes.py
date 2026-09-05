import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.ml.project_delay_service import predict_project_delay
from app.routes.sse_utils import stream_db_job
from app.schemas.project_delay import ProjectDelayPredictionResponse

router = APIRouter(
    prefix="/project-delay",
    tags=["Project Delay Prediction"]
)

logger = logging.getLogger(__name__)


@router.get(
    "/project/{project_id}",
    response_model=ProjectDelayPredictionResponse
)
def get_project_delay_prediction(
    project_id: int,
    db: Session = Depends(get_db),
):
    try:
        return predict_project_delay(db=db, project_id=project_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        logger.exception("Project delay prediction failed for project_id=%s", project_id)
        raise HTTPException(status_code=500, detail="Project delay prediction failed.")


@router.get("/project/{project_id}/stream")
async def stream_project_delay_prediction(project_id: int):
    return stream_db_job(
        predict_project_delay,
        done_message="Project delay prediction completed.",
        project_id=project_id,
    )
