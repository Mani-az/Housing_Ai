import pandas as pd
from sqlalchemy.orm import Session

from app.models.risk_data import RiskPredictionData


def load_risk_dataset(db: Session) -> pd.DataFrame:
    records = db.query(RiskPredictionData).all()

    data = []

    for record in records:
        data.append({
            "total_due_amount": record.total_due_amount,
            "total_paid_amount": record.total_paid_amount,
            "unpaid_amount": record.unpaid_amount,
            "average_delay_days": record.average_delay_days,
            "number_of_late_payments": record.number_of_late_payments,
            "inflation_rate": record.inflation_rate,
            "project_progress_percent": record.project_progress_percent,
            "risk_label": record.risk_label,
        })

    return pd.DataFrame(data)


def prepare_features_and_target(df: pd.DataFrame):
    feature_columns = [
        "total_due_amount",
        "total_paid_amount",
        "unpaid_amount",
        "average_delay_days",
        "number_of_late_payments",
        "inflation_rate",
        "project_progress_percent",
    ]

    target_column = "risk_label"

    X = df[feature_columns]
    y = df[target_column]

    return X, y