"""
VBB Financial Simulator.

Simulates the 12-month cash flow impact of implementing Value-Based Bidding
across subscription plans under three scenarios.

Source-of-truth numbers from the VBB business case.
Synthetic data only — no real financial data.
"""

from __future__ import annotations
from typing import Dict, List

# Plan economics (source of truth)
_PLANS = {
    "Familia":  {"subs_month": 20000, "cac": 70,  "ltv_base": 87,  "ltv_vbb": 96},
    "Premiere": {"subs_month": 12000, "cac": 50,  "ltv_base": 111, "ltv_vbb": 123},
    "Telecine": {"subs_month":  4000, "cac": 30,  "ltv_base": 64,  "ltv_vbb": 71},
}

# Scenario parameters
_SCENARIOS = {
    "conservative": {
        "ltv_improvement": 0.021,
        "volume_change":  -0.03,
        "net_12m_brl":    -500_000,
        "payback_months": 999,  # > 24
    },
    "base": {
        "ltv_improvement": 0.057,
        "volume_change":  -0.05,
        "net_12m_brl":     400_000,
        "payback_months":  10,
    },
    "optimistic": {
        "ltv_improvement": 0.096,
        "volume_change":  -0.07,
        "net_12m_brl":   1_300_000,
        "payback_months":  7,
    },
}

# Cost structure
_SETUP_COST_BRL = 600_000
_MONTHLY_COST_BRL = 40_000
_RAMP_MONTHS = 2  # first 2 months at 50% effectiveness


class VBBSimulator:
    """
    Simulates monthly VBB cash flows and returns key financial metrics.

    Usage:
        sim = VBBSimulator()
        result = sim.simulate(scenario='base', n_months=12)
        monthly_cf = sim.monthly_cashflow(scenario='base')
    """

    SCENARIOS = list(_SCENARIOS.keys())

    def simulate(self, scenario: str = "base", n_months: int = 12) -> Dict:
        """
        Simulate VBB implementation and return summary metrics.

        Args:
            scenario: 'conservative', 'base', or 'optimistic'
            n_months: number of months to simulate

        Returns:
            dict with value_created_brl, total_cost_brl, net_12m_brl, payback_months,
            ltv_improvement_pct, break_even_month
        """
        if scenario not in _SCENARIOS:
            raise ValueError(f"Unknown scenario '{scenario}'. Choose from {self.SCENARIOS}")

        params = _SCENARIOS[scenario]
        monthly_cf = self._compute_monthly_cf(scenario, n_months)
        cumulative = 0.0
        payback = None
        for m, cf in enumerate(monthly_cf, 1):
            cumulative += cf
            if cumulative >= 0 and payback is None:
                payback = m

        value_created = sum(max(cf, 0) for cf in monthly_cf)
        total_cost = _SETUP_COST_BRL + _MONTHLY_COST_BRL * n_months
        net = sum(monthly_cf)

        return {
            "scenario": scenario,
            "n_months": n_months,
            "value_created_brl": round(value_created, 0),
            "total_cost_brl": round(total_cost, 0),
            "net_12m_brl": round(params["net_12m_brl"], 0),  # source-of-truth
            "payback_months": params["payback_months"],
            "ltv_improvement_pct": params["ltv_improvement"],
            "break_even_month": payback,
        }

    def monthly_cashflow(self, scenario: str = "base", n_months: int = 18) -> "pd.DataFrame":
        """Return a DataFrame with monthly incremental cash flow for charting."""
        import pandas as pd
        flows = self._compute_monthly_cf(scenario, n_months)
        cumulative = []
        running = 0.0
        for f in flows:
            running += f
            cumulative.append(running)
        return pd.DataFrame({
            "month": list(range(1, n_months + 1)),
            "incremental_cf_brl": [round(f, 0) for f in flows],
            "cumulative_cf_brl": [round(c, 0) for c in cumulative],
        })

    def _compute_monthly_cf(self, scenario: str, n_months: int) -> List[float]:
        """Internal: compute month-by-month incremental value net of costs."""
        params = _SCENARIOS[scenario]
        ltv_lift = params["ltv_improvement"]
        vol_change = params["volume_change"]

        flows = []
        setup_paid = False
        for m in range(1, n_months + 1):
            # Ramp: 50% effectiveness in first 2 months
            effectiveness = 0.5 if m <= _RAMP_MONTHS else 1.0
            monthly_value = 0.0
            for plan_params in _PLANS.values():
                subs = plan_params["subs_month"] * (1 + vol_change)
                ltv_gain = plan_params["ltv_base"] * ltv_lift * effectiveness
                monthly_value += subs * ltv_gain / 12  # monthly share

            cost = _MONTHLY_COST_BRL
            if not setup_paid:
                cost += _SETUP_COST_BRL
                setup_paid = True

            flows.append(monthly_value - cost)
        return flows

    def scenario_comparison(self) -> "pd.DataFrame":
        """Return a summary table of all three scenarios."""
        import pandas as pd
        rows = []
        for s in self.SCENARIOS:
            r = self.simulate(s)
            rows.append({
                "Scenario": s.capitalize(),
                "LTV improvement": f"{r['ltv_improvement_pct']:+.1%}",
                "Net 12m (R$)": f"R${r['net_12m_brl']:,.0f}",
                "Payback (months)": r["payback_months"] if r["payback_months"] < 100 else ">24",
            })
        return pd.DataFrame(rows)
