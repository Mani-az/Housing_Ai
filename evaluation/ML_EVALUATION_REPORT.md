# Housing AI ML Evaluation

## Executive conclusion

The checked-in runtime already keeps the validated classifier/regressor as the
primary decision, preserves the healthy-operation safeguards, and exposes
contextual explanations. This report evaluates that canonical runtime rather
than presenting an older experimental copy as a separate release.

> Buyer-risk and project-delay data are synthetic scenario data. Their accuracy measures internal consistency with fabricated labels, not verified real-world predictive accuracy.

## Data inventory

| Module | Rows | Provenance | Evaluation method |
| --- | ---: | --- | --- |
| Member financial risk | 1,400 | Synthetic scenarios | Stratified 5-fold CV + fixed untouched 20% test |
| Project delay | 1,240 | Synthetic scenarios | Stratified 5-fold CV + fixed untouched 25% test |
| Economic forecast | 62 monthly rows | Real macro history, sparse by field | Chronological rolling-origin backtest |

## Core model quality

| Module | 5-fold classifier accuracy | Balanced accuracy | Macro F1 | Regressor MAE | R² |
| --- | ---: | ---: | ---: | ---: | ---: |
| Member risk | 91.43% | 89.10% | 89.27% | 3.17 risk-score points | 0.975 |
| Project delay | 99.92% | 99.86% | 99.89% | 5.25 months | 0.915 |

The project-delay classification score is unusually high because `delay_risk_level` is a deterministic band of the synthetic `predicted_delay_months` target. It must not be presented as evidence of 99.9% accuracy on real construction projects.

## Runtime policy and held-out check

The fixed hold-out test reproduces the split sizes used by the stored artifacts.

| Module | Metric | Canonical runtime |
| --- | --- | ---: |
| Member risk | Accuracy | 93.21% |
| Member risk | Macro F1 | 91.48% |
| Member risk | Score MAE | 3.09 |
| Member risk | Score R² | 0.978 |
| Project delay | Accuracy | 99.68% |
| Project delay | Macro F1 | 99.72% |
| Project delay | Months MAE | 5.05 |
| Project delay | Months R² | 0.924 |

### Runtime policy

- Member risk uses the stored classifier label and makes only the smallest score-boundary adjustment needed to keep the regressor score consistent with that label.
- Project delay uses the stored classifier label, retains the existing caps for genuinely healthy payment operations, and minimally clips predicted months into the selected label band.
- Contextual components and reason generation remain available and retain their existing meaning.
- No endpoint, route, request field, response field or serialized model artifact was removed or renamed.

## Economic forecasting

Economic forecasting is a regression/time-series problem, so classification accuracy is not meaningful. The appropriate measures are MAE/RMSE on chronological future observations.

The checked-in horizon hybrid was compared with a persistence baseline over
414 rolling-origin cases.

| Aggregate raw MAE across tested series/horizons | Value |
| --- | ---: |
| Canonical runtime | 13.102 |
| Pure persistence baseline | 13.060 |

Pure persistence is still marginally better overall. This means the available
macro data does not justify a more complex economic model yet.

Selected one-month MAE results:

| Series | Canonical runtime | Persistence |
| --- | ---: | ---: |
| General inflation rate | 1.95 | 1.92 |
| Construction cost growth | 3.79 | 3.60 |
| USD growth | 12.89 | 12.73 |
| Housing CPI growth | 0.48 | 0.47 |

Housing CPI has only 17 observed values, with just 9 one-month test cases and no valid 12-month test. Long-horizon results must therefore be treated as low confidence.

## Recommendation

1. Use the canonical runtime as a prototype release, not as proof of real-world accuracy.
2. Keep the current model artifacts and version the evaluation report with them.
3. Collect real outcome labels:
   - member payment state at a future cutoff,
   - realized project delay months,
   - point-in-time feature snapshots to avoid leakage.
4. Re-evaluate with time-based or project-grouped splits before making operational claims.
5. Expand and refresh macroeconomic history before attempting a more complex forecaster.

## Professor-ready automated test

Two backend files make the evaluation easy to reproduce without installing pytest:

```text
backend/app/scripts/evaluate_ml_accuracy.py
backend/tests/test_ml_accuracy.py
```

From the backend directory, run:

```bash
python -m unittest discover -s tests -p "test_ml_accuracy.py" -v
```

The suite checks five explicit quality gates: member-risk cross-validation, member-risk held-out runtime, project-delay cross-validation, project-delay held-out runtime, and chronological economic rolling-origin behavior. The successful reference run is stored in `ml_evaluation/PROFESSOR_TEST_OUTPUT.txt`.

For a presentation-friendly summary or machine-readable output:

```bash
python -m app.scripts.evaluate_ml_accuracy
python -m app.scripts.evaluate_ml_accuracy --json
```

The test/evaluator use the accuracy-calibrated `prediction_services_v2.py`
shipped in the backend package. A separate comparison backend is optional and
only needed for historical experiments.

## Reproduction

From the workspace root:

```bash
python ml_evaluation/evaluate_models.py > ml_evaluation/metrics.json
```

The evaluation script defaults to the canonical backend package. Pass
`--improved-backend` only when comparing a separately versioned historical
experiment.
