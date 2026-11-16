"""
LTV Model for subscription platforms.

Computes expected LTV by plan and D7 class, and estimates the
portfolio-level LTV per media R$ under different subscriber mix scenarios.

Source of truth: VBB business case (synthetic data).
"""

from __future__ import annotations
from typing import Dict

# Plan-level LTV (R$) — source of truth
PLAN_LTV = {
    "Familia":  87.0,
    "Premiere": 111.0,
    "Telecine": 64.0,
}

# D7 class multipliers — source of truth
D7_MULTIPLIERS = {
    "Heavy":    2.20,
    "Moderate": 1.00,
    "Critical": 0.25,
}

# Current mix (baseline)
BASELINE_MIX = {"Heavy": 0.25, "Moderate": 0.35, "Critical": 0.40}

# Average CAC across plans — source of truth
AVG_CAC = 59.0


class LTVModel:
    """LTV computation and scenario analysis."""

    def compute_expected_ltv(self, plan: str, d7_class: str) -> float:
        """
        Return expected LTV for a subscriber in a given plan × D7 class.

        Args:
            plan: 'Familia', 'Premiere', or 'Telecine'
            d7_class: 'Heavy', 'Moderate', or 'Critical'

        Returns:
            Expected LTV in BRL.
        """
        if plan not in PLAN_LTV:
            raise ValueError(f"Unknown plan '{plan}'")
        if d7_class not in D7_MULTIPLIERS:
            raise ValueError(f"Unknown d7_class '{d7_class}'")
        return round(PLAN_LTV[plan] * D7_MULTIPLIERS[d7_class], 2)

    def compute_portfolio_ltv(self, mix: Dict[str, float]) -> float:
        """
        Compute weighted average LTV given a subscriber mix.

        Args:
            mix: dict with keys 'Heavy', 'Moderate', 'Critical' summing to 1.0

        Returns:
            Weighted average LTV in BRL (cross-plan).
        """
        base_ltv = 92.0  # cross-plan base
        return round(
            sum(base_ltv * D7_MULTIPLIERS[cls] * share for cls, share in mix.items()),
            2,
        )

    def compute_ltv_per_media_dollar(self, mix: Dict[str, float]) -> float:
        """
        Return the LTV delivered per R$ of media investment under a given mix,
        normalised to the baseline mix.

        Args:
            mix: {'Heavy': float, 'Moderate': float, 'Critical': float}

        Returns:
            Relative improvement vs baseline (e.g. 1.057 = +5.7%).
        """
        baseline = self.compute_portfolio_ltv(BASELINE_MIX)
        scenario = self.compute_portfolio_ltv(mix)
        return round(scenario / baseline, 4)

    def scenario_table(self) -> "pd.DataFrame":
        """Return scenario comparison table matching the business case."""
        import pandas as pd
        scenarios = {
            "Today (baseline)":  {"Heavy": 0.25, "Moderate": 0.35, "Critical": 0.40},
            "Conservative":      {"Heavy": 0.28, "Moderate": 0.36, "Critical": 0.37},
            "Base":              {"Heavy": 0.30, "Moderate": 0.37, "Critical": 0.33},
            "Optimistic":        {"Heavy": 0.33, "Moderate": 0.38, "Critical": 0.29},
        }
        rows = []
        baseline_ltv = self.compute_portfolio_ltv(BASELINE_MIX)
        for name, mix in scenarios.items():
            ltv = self.compute_portfolio_ltv(mix)
            improvement = (ltv - baseline_ltv) / baseline_ltv
            rows.append({
                "Scenario": name,
                "Heavy%": f"{mix['Heavy']:.0%}",
                "Moderate%": f"{mix['Moderate']:.0%}",
                "Critical%": f"{mix['Critical']:.0%}",
                "Portfolio LTV (R$)": ltv,
                "LTV improvement": f"{improvement:+.1%}",
            })
        return pd.DataFrame(rows)
