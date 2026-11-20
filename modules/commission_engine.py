import pandas as pd


def calculate_attainment(actual_sales, sales_target):
    """Return attainment percentage. Returns None if the target is zero."""
    if pd.isna(actual_sales) or pd.isna(sales_target):
        raise ValueError("Missing sales value")
    if actual_sales < 0 or sales_target < 0:
        raise ValueError("Negative values are not allowed")
    if sales_target == 0:
        return None
    return round(actual_sales / sales_target * 100, 2)


def get_commission_rate(attainment):
    """Pick the commission rate based on attainment percentage."""
    if attainment is None:
        return 0.0
    if attainment < 80:
        return 0.02
    elif attainment < 100:
        return 0.05
    elif attainment <= 120:
        return 0.08
    else:
        return 0.12


def calculate_payout(actual_sales, rate):
    """Payout = actual sales x rate."""
    return round(actual_sales * rate, 2)


def process_sales_data(df):
    """Add attainment, rate and payout columns to a sales DataFrame."""
    result = df.copy()
    attainments, rates, payouts = [], [], []

    for _, row in result.iterrows():
        att = calculate_attainment(row["actual_sales"], row["sales_target"])
        rate = get_commission_rate(att)
        payout = calculate_payout(row["actual_sales"], rate)
        attainments.append(att)
        rates.append(rate)
        payouts.append(payout)

    result["attainment_pct"] = attainments
    result["commission_rate"] = rates
    result["payout"] = payouts
    return result