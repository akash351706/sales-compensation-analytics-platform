import pandas as pd
import plotly.express as px
import streamlit as st

from modules.analytics import compute_kpis
from modules.commission_engine import process_sales_data
from modules.data_validation import validate_sales_data

def show_table(data, use_container_width=True):




    html = data.to_html(index=False, border=0)




    st.markdown(html, unsafe_allow_html=True)

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

# ---------- Validate ----------
errors = validate_sales_data(df)
missing_columns = any(e["row"] == 0 for e in errors)
if missing_columns:
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
results = process_sales_data(valid_df)
kpis = compute_kpis(results)

tab_dash, tab_data, tab_valid = st.tabs(["Dashboard", "Sales Data", "Validation"])

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
    show_table(ranking[["employee_name", "attainment_pct", "commission_rate", "payout"]],
                 use_container_width=True)

# ---------- Sales data tab ----------
with tab_data:
    st.subheader("Calculated results")
    show_table(results, use_container_width=True)

# ---------- Validation tab ----------
with tab_valid:
    if errors:
        st.error(f"{len(errors)} issue(s) found. Rows with issues were left out of the calculation.")
        show_table(pd.DataFrame(errors), use_container_width=True)
    else:
        st.success("No validation errors found.")