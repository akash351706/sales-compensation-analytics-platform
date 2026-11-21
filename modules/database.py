import sqlite3

import pandas as pd

from modules.commission_engine import DEFAULT_PLAN, process_sales_data

DB_PATH = "database/commission.db"
SCHEMA_PATH = "database/schema.sql"


def get_connection():
    """Open the database and make sure all tables exist."""
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    return conn


def save_results(conn, results_df, plan, plan_name="Plan"):
    """Save employees, sales records, the plan and calculation results."""
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO commission_plans "
        "(plan_name, tier1_limit, tier2_limit, tier3_limit, rate1, rate2, rate3, rate4) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (plan_name, float(plan["tier1_limit"]), float(plan["tier2_limit"]),
         float(plan["tier3_limit"]), float(plan["rate1"]), float(plan["rate2"]),
         float(plan["rate3"]), float(plan["rate4"])),
    )
    plan_id = cur.lastrowid

    for _, r in results_df.iterrows():
        cur.execute(
            "INSERT OR REPLACE INTO employees (employee_id, employee_name, department) "
            "VALUES (?, ?, ?)",
            (str(r["employee_id"]), str(r["employee_name"]), str(r["department"])),
        )
        cur.execute(
            "INSERT OR REPLACE INTO sales_records "
            "(employee_id, month, sales_target, actual_sales) VALUES (?, ?, ?, ?)",
            (str(r["employee_id"]), str(r["month"]),
             float(r["sales_target"]), float(r["actual_sales"])),
        )
        attainment = None if pd.isna(r["attainment_pct"]) else float(r["attainment_pct"])
        cur.execute(
            "INSERT INTO calculation_results "
            "(employee_id, month, plan_id, attainment_pct, commission_rate, payout) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (str(r["employee_id"]), str(r["month"]), plan_id, attainment,
             float(r["commission_rate"]), float(r["payout"])),
        )

    conn.commit()
    return plan_id


def run_query(conn, sql):
    """Run a SQL query and return a DataFrame."""
    return pd.read_sql_query(sql, conn)


if __name__ == "__main__":
    data = pd.read_csv("data/sales_data.csv")
    results = process_sales_data(data, DEFAULT_PLAN)

    connection = get_connection()
    save_results(connection, results, DEFAULT_PLAN, "Default plan")

    print("\nTotal sales per employee:")
    print(run_query(connection,
        "SELECT employee_id, SUM(actual_sales) AS total_sales "
        "FROM sales_records GROUP BY employee_id"))

    print("\nResults ordered by payout:")
    print(run_query(connection,
        "SELECT employee_id, attainment_pct, payout "
        "FROM calculation_results ORDER BY payout DESC"))

    connection.close()