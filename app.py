import pandas as pd
import plotly.express as px
import streamlit as st

from modules.analytics import compute_kpis
from modules.commission_engine import DEFAULT_PLAN, process_sales_data
from modules.data_validation import validate_sales_data


def show_table(data):
    """Show a table without pyarrow (blocked on this PC)."""
    html = data.to_html(index=False, border=0)
    st.markdown(f'<div style="overflow-x:auto">{html}</div>', unsafe_allow_html=True)


st.set_page_config(page_title="Sales Compensation Analytics", layout="wide")
st.title("Sales Compensation Analytics & Commission Automation")
st.caption("Independent portfolio project with synthetic demo data.")

# ---------- Upload ----------
with open("data/sales_data.csv", "rb") as f:
    sample_bytes = f.read()
st.sidebar.download_button("Download sample CSV", sample_bytes,
                           file_name="sales_data.csv", mime="text/csv")
uploaded = st.sidebar.file_uploader("Upload a sales CSV", type="csv")

if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.sidebar.success(f"Using uploaded file: {uploaded.name}")
else:
    df = pd.read_csv("data/sales_data.csv")
    st.sidebar.info("Using the built-in sample data")

tab_dash, tab_data, tab_plan, tab_valid = st.tabs(
    ["Dashboard", "Sales Data", "Commission Plan", "Validation"])

# ---------- Commission Plan tab ----------
with tab_plan:
    st.subheader("Commission plan")
    st.caption("Change the tiers or rates. Payouts recalculate automatically.")
    st.write("**Attainment limits (%)**")
    p1, p2, p3 = st.columns(3)
    tier1 = p1.number_input("Tier 1 ends below", value=DEFAULT_PLAN["tier1_limit"], step=1)
    tier2 = p2.number_input("Tier 2 ends below", value=DEFAULT_PLAN["tier2_limit"], step=1)
    tier3 = p3.number_input("Tier 3 ends at", value=DEFAULT_PLAN["tier3_limit"], step=1)
    st.write("**Commission rates**")
    r1, r2, r3, r4 = st.columns(4)
    rate1 = r1.number_input("Rate: below tier 1", value=DEFAULT_PLAN["rate1"], step=0.01, format="%.2f")
    rate2 = r2.number_input("Rate: tier 2", value=DEFAULT_PLAN["rate2"], step=0.01, format="%.2f")
    rate3 = r3.number_input("Rate: tier 3", value=DEFAULT_PLAN["rate3"], step=0.01, format="%.2f")
    rate4 = r4.number_input("Rate: above tier 3", value=DEFAULT_PLAN["rate4"], step=0.01, format="%.2f")

plan = {
    "tier1_limit": tier1, "tier2_limit": tier2, "tier3_limit": tier3,
    "rate1": rate1, "rate2": rate2, "rate3": rate3, "rate4": rate4,
}

if not (tier1 < tier2 <= tier3):
    st.error("Plan error: the tier limits must increase (tier 1 < tier 2 <= tier 3).")
    st.stop()

# ---------- Validate ----------
errors = validate_sales_data(df)
if any(e["row"] == 0 for e in errors):
    st.error(errors[0]["message"])
    st.stop()

bad_rows = {e["row"] - 2 for e in errors}
valid_df = df.drop(index=list(bad_rows)).copy()
if valid_df.empty:
    st.warning("No valid rows to process.")
    st.stop()

valid_df["sales_target"] = pd.to_numeric(valid_df["sales_target"])
valid_df["actual_sales"] = pd.to_numeric(valid_df["actual_sales"])

# ---------- Calculate ----------
results = process_sales_data(valid_df, plan)
kpis = compute_kpis(results)

# ---------- Dashboard tab ----------
with tab_dash:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total sales", f"{kpis['total_sales']:,.0f}")
    c2.metric("Total payout", f"{kpis['total_payout']:,.0f}")
    c3.metric("Average attainment", f"{kpis['avg_attainment']:.1f}%")
    c4.metric("Employees at/above target", kpis["above_target"])
    c5.metric("Top performer", kpis["top_performer"])

    left, right = st.columns(2)
    with left:
        melted = results.melt(id_vars="employee_name",
                              value_vars=["sales_target", "actual_sales"],
                              var_name="type", value_name="amount")
        fig1 = px.bar(melted, x="employee_name", y="amount", color="type",
                      barmode="group", title="Actual vs target by employee")
        st.plotly_chart(fig1, use_container_width=True)
    with right:
        fig2 = px.bar(results, x="employee_name", y="payout",
                      title="Payout by employee")
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.histogram(results, x="attainment_pct", nbins=10,
                        title="Attainment distribution")
    st.plotly_chart(fig3, use_container_width=True)

    if results["month"].nunique() > 1:
        monthly = results.groupby("month", as_index=False)[["actual_sales", "payout"]].sum()
        fig4 = px.line(monthly, x="month", y=["actual_sales", "payout"],
                       markers=True, title="Monthly trend")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Ranking by attainment")
    ranking = results.sort_values("attainment_pct", ascending=False)
    show_table(ranking[["employee_name", "attainment_pct", "commission_rate", "payout"]])

# ---------- Sales data tab ----------
with tab_data:
    st.subheader("Calculated results")
    show_table(results)

# ---------- Validation tab ----------
with tab_valid:
    if errors:
        st.error(f"{len(errors)} issue(s) found. Rows with issues were left out of the calculation.")
        show_table(pd.DataFrame(errors))
    else:
        st.success("No validation errors found.")