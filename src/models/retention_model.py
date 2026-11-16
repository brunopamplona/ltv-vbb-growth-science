"""
Retention Model for subscription platforms.

Encodes observed survival curves (from source-of-truth business case)
and provides expected lifetime computation per plan.

Synthetic data only — no real subscriber data.
"""

from __future__ import annotations
from typing import Dict

# Survival rates (1 - cumulative cancellation) per month per plan
# Source of truth: VBB business case retention curves
_SURVIVAL_CURVES: Dict[str, Dict[int, float]] = {
    "Familia": {
        0: 1.000, 1: 0.670, 2: 0.360, 3: 0.265,
        4: 0.230, 5: 0.185, 6: 0.045, 7: 0.020,
        8: 0.005, 9: 0.000, 10: 0.000, 11: 0.000, 12: 0.000,
    },
    "Premiere": {
        0: 1.000, 1: 0.800, 2: 0.705, 3: 0.620,
        4: 0.505, 5: 0.445, 6: 0.365, 7: 0.290,
        8: 0.190, 9: 0.140, 10: 0.025, 11: 0.012, 12: 0.010,
    },
    "Telecine": {
        0: 1.000, 1: 0.847, 2: 0.742, 3: 0.675,
        4: 0.635, 5: 0.515, 6: 0.400, 7: 0.337,
        8: 0.263, 9: 0.205, 10: 0.172, 11: 0.032, 12: 0.027,
    },
}

# Source-of-truth expected lifetimes (months)
_EXPECTED_LIFETIMES = {
    "Familia":  2.3,
    "Premiere": 4.6,
    "Telecine": 5.4,
}


class RetentionModel:
    """Survival curves and expected lifetime per subscription plan."""

    PLANS = list(_SURVIVAL_CURVES.keys())

    def get_survival_curve(self, plan: str) -> Dict[int, float]:
        """
        Return the monthly survival curve for a plan.

        Args:
            plan: 'Familia', 'Premiere', or 'Telecine'

        Returns:
            Dict mapping month → survival rate (0–1).
        """
        if plan not in _SURVIVAL_CURVES:
            raise ValueError(f"Unknown plan '{plan}'. Choose from {self.PLANS}")
        return _SURVIVAL_CURVES[plan].copy()

    def compute_expected_lifetime(self, plan: str) -> float:
        """
        Return the expected subscriber lifetime in months.

        Uses the source-of-truth value from the business case
        (area under the survival curve).

        Args:
            plan: 'Familia', 'Premiere', or 'Telecine'

        Returns:
            Expected lifetime in months.
        """
        if plan not in _EXPECTED_LIFETIMES:
            raise ValueError(f"Unknown plan '{plan}'")
        return _EXPECTED_LIFETIMES[plan]

    def to_dataframe(self) -> "pd.DataFrame":
        """Return all survival curves as a tidy DataFrame."""
        import pandas as pd
        rows = []
        for plan, curve in _SURVIVAL_CURVES.items():
            for month, survival in curve.items():
                rows.append({
                    "plan": plan,
                    "month": month,
                    "survival_rate": survival,
                    "cumulative_cancellation": round(1 - survival, 4),
                    "hazard": round(
                        (1 - (survival / prev_s))
                        if month > 0 and (prev_s := _SURVIVAL_CURVES[plan].get(month - 1, survival)) > 0
                        else 0, 4
                    ),
                })
        return pd.DataFrame(rows)
