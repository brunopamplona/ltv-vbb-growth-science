"""
D7 Behavioral Classifier for subscription platforms.

Implements the deterministic rule-based classification of new paid subscribers
into Heavy / Moderate / Critical classes based on the first 7 days of behavior.

All thresholds are from the VBB business case source of truth.
Synthetic data only — no real subscriber data.
"""

from __future__ import annotations

# LTV multipliers per class (base LTV = R$92)
_BASE_LTV = 92.0
_LTV_MULTIPLIERS = {
    "Heavy":    2.20,
    "Moderate": 1.00,
    "Critical": 0.25,
}

# Plan-level average LTV (source of truth)
_PLAN_LTV = {
    "Familia":  87.0,
    "Premiere": 111.0,
    "Telecine": 64.0,
}


class D7Classifier:
    """
    Rule-based D7 subscriber classifier.

    Classification order (to avoid overlap):
        1. Critical: 0 plays in 7 days OR >4 days without login
        2. Heavy: ≥3 active days AND ≥2 plays
        3. Moderate: everything else (1 play OR 1–2 active days)
    """

    def classify(self, days_active: int, plays: int) -> str:
        """
        Classify a subscriber based on D7 behavioral signals.

        Args:
            days_active: Number of days with at least one login in D0–D7.
            plays: Number of content plays in D0–D7.

        Returns:
            One of: 'Critical', 'Heavy', 'Moderate'
        """
        inactive_days = 7 - days_active

        if plays == 0 or inactive_days > 4:
            return "Critical"
        if days_active >= 3 and plays >= 2:
            return "Heavy"
        return "Moderate"

    def predict_ltv(self, d7_class: str, plan: str | None = None) -> float:
        """
        Predict expected LTV given D7 class and optional plan.

        If plan is provided, uses plan-level base LTV × D7 multiplier.
        Otherwise uses the cross-plan base LTV (R$92) × multiplier.

        Args:
            d7_class: 'Heavy', 'Moderate', or 'Critical'
            plan: 'Familia', 'Premiere', or 'Telecine' (optional)

        Returns:
            Expected LTV in BRL.
        """
        if d7_class not in _LTV_MULTIPLIERS:
            raise ValueError(f"Unknown d7_class: {d7_class}. Use 'Heavy', 'Moderate', or 'Critical'.")

        multiplier = _LTV_MULTIPLIERS[d7_class]

        if plan is not None:
            if plan not in _PLAN_LTV:
                raise ValueError(f"Unknown plan: {plan}. Use 'Familia', 'Premiere', or 'Telecine'.")
            base = _PLAN_LTV[plan]
        else:
            base = _BASE_LTV

        return round(base * multiplier, 2)

    def classify_dataframe(self, df, days_col: str = "days_active_d7", plays_col: str = "plays_d7") -> "pd.Series":
        """Vectorised classification over a DataFrame."""
        import pandas as pd
        return df.apply(lambda row: self.classify(row[days_col], row[plays_col]), axis=1)
