# ML Data Audit & Improvement Plan

## Executive summary

The uploaded data is usable for the next ML iteration, with a critical provenance caveat, but the models should not all be handled the same way.

- `buyer_risk_dataset.csv`: 1,400 synthetic scenario rows, 28 columns, no missing values. Best handled as a **risk-score regression + thresholded label** model for prototype decision support.
- `construction_delay_dataset.csv`: 1,240 synthetic scenario rows, 15 columns, no missing values. Best handled as **delay-month regression + contextual risk band** for prototype decision support.
- `economic_indicators.csv`: 62 real monthly macro-indicator rows, but several columns are sparse/stale. Best handled as a **hybrid lag/rolling forecast**, not a heavy ML model.
- `tehran_properties.xlsx`: 139,749 apartment records and 279 standardized Tehran neighborhoods.


## Data provenance clarification

Important correction from the project owner: only `economic_indicators.csv` should be treated as real-world data. The remaining ML training datasets, especially `buyer_risk_dataset.csv` and `construction_delay_dataset.csv`, are synthetic/fabricated scenario data created for the prototype.

This changes how the metrics must be interpreted:

- Buyer-risk and project-delay validation metrics show that the models learned the synthetic scenario rules consistently. They should not be presented as real-world predictive accuracy.
- The buyer-risk and project-delay models are still useful for demo, decision-support workflow validation, and consistent risk scoring inside the prototype.
- The economic module is the only part that can be described as based on real historical indicators, but it remains limited by sparse and stale fields.
- For thesis/defense wording, use “synthetic scenario-trained model” for buyer/project models and “real macro-indicator hybrid forecast” for the economic model.

Recommended defense wording:

> Buyer-risk and construction-delay models were trained on synthetic scenario data designed to simulate cooperative housing payment and construction behavior. Therefore, their evaluation measures internal consistency on the simulated dataset rather than verified real-world accuracy. The economic forecasting component uses real macroeconomic indicator data and is handled conservatively with lag/rolling features due to limited coverage.

## Buyer risk findings

`risk_label` is a deterministic bin of `risk_score`:

| label | score range | rows |
|---|---:|---:|
| low | < 35 | 788 |
| medium | 35–64.999 | 348 |
| high | >= 65 | 264 |

The current checked-in CSV contains 1,400 rows. Any report that refers to the
older 1,000-row distribution is stale and must not be used as the current
evaluation summary.

Recommended prediction pattern:

1. Predict `risk_score` from payment, overdue, delay, and macro pressure features.
2. Convert score to `risk_label` using the same thresholds.
3. Return explanation reasons based on the top pressure indicators.

Current quality-gate results (5-fold stratified CV plus a fixed held-out
runtime check) are:

| metric | value |
|---|---:|
| 5-fold classifier accuracy | 0.914 |
| 5-fold classifier macro F1 | 0.893 |
| 5-fold score MAE | 3.17 |
| 5-fold score R² | 0.975 |
| held-out classifier accuracy | 0.932 |
| held-out classifier macro F1 | 0.915 |
| held-out score MAE | 3.09 |

Important features from the dataset are payment completion, due-unpaid ratio, unpaid ratio, average delay days, max delay days, and paid-late count.

## Project delay findings

`delay_risk_level` is a deterministic band of `predicted_delay_months`:

| label | delay range |
|---|---:|
| acceptable_delay | <= 6 months |
| low | > 6 and <= 12 months |
| medium | > 12 and <= 24 months |
| high | > 24 and <= 60 months |
| critical | > 60 months |

Recommended prediction pattern:

1. Predict `predicted_delay_months`.
2. Convert delay months to a contextual risk band.
3. Return risk drivers such as cash-flow pressure, high-risk member ratio, overdue ratio, and economic pressure.

Current quality-gate results (5-fold stratified CV plus a fixed held-out
runtime check) are:

| metric | value |
|---|---:|
| 5-fold months MAE | 5.25 months |
| 5-fold months R² | 0.916 |
| 5-fold classifier accuracy | 0.999 |
| 5-fold classifier macro F1 | 0.999 |
| held-out months MAE | 5.05 months |
| held-out classifier accuracy | 0.997 |
| held-out classifier macro F1 | 0.997 |

## Economic data findings

Economic data coverage:

| field | non-null rows | last non-null date | last value |
|---|---:|---:|---:|
| general_inflation_rate | 57 | 2026-03-01 | 50.0 |
| construction_cost_growth | 40 | 2025-06-01 | 70.5882 |
| usd_growth | 39 | 2025-05-01 | 116.2146 |
| housing_cpi_growth | 17 | 2025-09-01 | 36.0539 |

Because several macro series are sparse or stale, the economic module should use a conservative hybrid forecaster:
- last known value
- 3-month and 6-month rolling averages
- bounded trend adjustment
- confidence based on recency and number of usable observations

## Recommended backend integration

Keep existing API fields stable, then add these optional fields:

```json
{
  "risk_score": 72.4,
  "risk_label": "high",
  "confidence": "medium",
  "reasons": ["High overdue amount ratio", "Repeated late payments"]
}
```

For project delay:

```json
{
  "predicted_delay_months": 18.5,
  "delay_risk_level": "medium",
  "confidence": "medium",
  "reasons": ["Cash-flow pressure is elevated", "High-risk member ratio is significant"]
}
```

## Files in this pack

- `train_models_v2.py`: retrains buyer-risk and project-delay models.
- `prediction_services_v2.py`: drop-in prediction helpers for backend services.
- `models/buyer_risk_v2.joblib`: trained buyer risk artifact.
- `models/project_delay_v2.joblib`: trained project delay artifact.
- `models/economic_forecaster_v2.joblib`: hybrid economic forecaster artifact.
- `metrics.json`: validation and data coverage metrics.
- `data_outputs/tehran_neighborhood_options.json`: clean frontend dropdown options.
- `data_outputs/tehran_neighborhood_summary.csv`: neighborhood stats summary.
