"""Professor/CI-ready quality gates for the Housing AI ML prototype.

Run with Python only (no extra test dependency):
    python -m unittest discover -s tests -p "test_ml_accuracy.py" -v

Pytest can also discover this file if it is already installed:
    pytest -q -s tests/test_ml_accuracy.py

These thresholds validate repeatability on the supplied datasets. They do not
claim verified accuracy on real cooperative-housing outcomes because the buyer
and delay labels are synthetic.
"""

import unittest

from app.scripts.evaluate_ml_accuracy import evaluate_all


class TestMLAccuracy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = evaluate_all()
        print("\nML provenance warning:", cls.results["warning"])

    def test_member_risk_cross_validation(self):
        result = self.results["buyer_risk"]
        classifier = result["five_fold_classifier"]
        regressor = result["five_fold_regressor"]

        print(
            "\nMember risk 5-fold: "
            f"accuracy={classifier['accuracy']:.4f}, "
            f"macro_f1={classifier['macro_f1']:.4f}, "
            f"score_mae={regressor['mae']:.4f}, "
            f"r2={regressor['r2']:.4f}"
        )

        self.assertGreaterEqual(classifier["accuracy"], 0.85)
        self.assertGreaterEqual(classifier["macro_f1"], 0.85)
        self.assertLessEqual(regressor["mae"], 4.50)
        self.assertGreaterEqual(regressor["r2"], 0.90)

    def test_member_risk_runtime_on_held_out_data(self):
        result = self.results["buyer_risk"]
        classifier = result["runtime_classifier"]
        regressor = result["runtime_regressor"]

        print(
            "\nMember risk held-out runtime: "
            f"accuracy={classifier['accuracy']:.4f}, "
            f"macro_f1={classifier['macro_f1']:.4f}, "
            f"score_mae={regressor['mae']:.4f}"
        )

        self.assertGreaterEqual(result["held_out_test_rows"], 250)
        self.assertGreaterEqual(classifier["accuracy"], 0.88)
        self.assertGreaterEqual(classifier["macro_f1"], 0.85)
        self.assertLessEqual(regressor["mae"], 4.50)

    def test_project_delay_cross_validation(self):
        result = self.results["project_delay"]
        classifier = result["five_fold_classifier"]
        regressor = result["five_fold_regressor"]

        print(
            "\nProject delay 5-fold: "
            f"accuracy={classifier['accuracy']:.4f}, "
            f"macro_f1={classifier['macro_f1']:.4f}, "
            f"months_mae={regressor['mae']:.4f}, "
            f"r2={regressor['r2']:.4f}"
        )

        self.assertGreaterEqual(classifier["accuracy"], 0.95)
        self.assertGreaterEqual(classifier["macro_f1"], 0.95)
        self.assertLessEqual(regressor["mae"], 7.00)
        self.assertGreaterEqual(regressor["r2"], 0.85)

    def test_project_delay_runtime_on_held_out_data(self):
        result = self.results["project_delay"]
        classifier = result["runtime_classifier"]
        regressor = result["runtime_regressor"]

        print(
            "\nProject delay held-out runtime: "
            f"accuracy={classifier['accuracy']:.4f}, "
            f"macro_f1={classifier['macro_f1']:.4f}, "
            f"months_mae={regressor['mae']:.4f}"
        )

        self.assertGreaterEqual(result["held_out_test_rows"], 300)
        self.assertGreaterEqual(classifier["accuracy"], 0.95)
        self.assertGreaterEqual(classifier["macro_f1"], 0.95)
        self.assertLessEqual(regressor["mae"], 7.00)

    def test_economic_forecast_walk_forward(self):
        result = self.results["economic_forecast"]

        print(
            "\nEconomic rolling-origin: "
            f"cases={result['test_cases']}, "
            f"model_mae={result['aggregate_model_mae']:.4f}, "
            f"persistence_mae={result['aggregate_persistence_mae']:.4f}"
        )

        self.assertEqual(result["evaluation"], "chronological_rolling_origin")
        self.assertGreaterEqual(result["test_cases"], 400)
        # Sparse macro history does not justify claiming superiority to persistence.
        # The candidate must remain within 2% of that strong conservative baseline.
        self.assertLessEqual(
            result["aggregate_model_mae"],
            result["aggregate_persistence_mae"] * 1.02,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
