import pandas as pd


def compute_kpis(df):
    """Return the headline numbers shown on the dashboard."""
    attainment = pd.to_numeric(df["attainment_pct"], errors="coerce")

    top_performer = "N/A"
    if attainment.notna().any():
        top_performer = df.loc[attainment.idxmax(), "employee_name"]

    return {
        "total_sales": df["actual_sales"].sum(),
        "total_payout": df["payout"].sum(),
        "avg_attainment": attainment.mean(),
        "above_target": int((attainment >= 100).sum()),
        "top_performer": top_performer,
    }