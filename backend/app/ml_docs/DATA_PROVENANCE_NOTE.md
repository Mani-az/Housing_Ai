# Data Provenance Note

Project clarification: only `economic_indicators.csv` should be treated as real-world data.

| dataset | provenance | recommended interpretation |
|---|---|---|
| `economic_indicators.csv` | Real macroeconomic indicator data | Use for conservative economic forecasting with lag/rolling features. |
| `buyer_risk_dataset.csv` | Synthetic/fabricated scenario data | Use for prototype member-risk scoring and demo consistency, not real-world accuracy claims. |
| `construction_delay_dataset.csv` | Synthetic/fabricated scenario data | Use for prototype project-delay scoring and demo consistency, not real-world accuracy claims. |
| `tehran_properties.xlsx` | Historical Tehran property listing data as provided | Use for dropdown normalization and descriptive neighborhood statistics, not direct project-risk training unless provenance is separately defended. |

## Defense-safe wording

The buyer-risk and construction-delay components are trained on synthetic scenario datasets designed to emulate cooperative housing payment and construction-delay behavior. Their validation metrics demonstrate consistency within the simulated prototype environment. The economic forecasting component uses real macroeconomic indicators and applies conservative lag/rolling logic due to limited and partially stale observations.
