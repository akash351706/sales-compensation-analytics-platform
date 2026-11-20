import pandas as pd

DEFAULT_PLAN = {
    "tier1_limit": 80,
    "tier2_limit": 100,
    "tier3_limit": 120,
    "rate1": 0.02,
    "rate2": 0.05,
    "rate3": 0.08,
    "rate4": 0.12,
}


def calculate_attainment(actual_sales, sales_target):
    """Return attainment percentage. Returns None if the target is zero."""
    if pd.isna(actual_sales) or pd.isna(sales_target):
        raise ValueError("Missing sales value")
    if actual_sales < 0 or sales_target < 0:
        raise ValueError("Negative values are not allowed")
    if sales_target == 0:
        return None
    return round(actual_sales / sales_target * 100, 2)


def get_commission_rate(attainment, plan=None):
    """Pick the commission rate based on attainment and the plan."""
    if plan is None:
        plan = DEFAULT_PLAN
    if attainment is None:
        return 0.0
    if attainment < plan["tier1_limit"]:
        return plan["rate1"]
    elif attainment < plan["tier2_limit"]:
        return plan["rate2"]
    elif attainment <= plan["tier3_limit"]:
        return plan["rate3"]
    else:
        return plan["rate4"]


def calculate_payout(actual_sales, rate):
    """Payout = actual sales x rate."""
    return round(actual_sales * rate, 2)


def process_sales_data(df, plan=None):
    """Add attainment, rate and payout columns to a sales DataFrame."""
    result = df.copy()
    attainments, rates, payouts = [], [], []

    for _, row in result.iterrows():
        att = calculate_attainment(row["actual_sales"], row["sales_target"])
        rate = get_commission_rate(att, plan)
        payout = calculate_payout(row["actual_sales"], rate)
        attainments.append(att)
        rates.append(rate)
        payouts.append(payout)

    result["attainment_pct"] = attainments
    result["commission_rate"] = rates
    result["payout"] = payouts
    return result