import pandas as pd

from modules.commission_engine import (
    DEFAULT_PLAN,
    calculate_attainment,
    calculate_payout,
    get_commission_rate,
)
from modules.data_validation import validate_sales_data


def _case(issue, checks, evidence, root_cause, resolution, verification):
    return {
        "issue": issue,
        "checks": checks,
        "evidence": evidence,
        "root_cause": root_cause,
        "resolution": resolution,
        "verification": verification,
    }


def _find_row(df, employee_id):
    rows = df[df["employee_id"] == employee_id]
    if rows.empty:
        return None
    return rows.iloc[0]


def commission_too_low(df, employee_id, plan=None):
    plan = plan or DEFAULT_PLAN
    issue = f"{employee_id} says the commission is too low"
    checks = ["Find the sales record", "Check target and actual sales",
              "Work out attainment", "Match attainment to the plan tier"]
    row = _find_row(df, employee_id)
    if row is None:
        return _case(issue, checks, [f"No record found for {employee_id}"],
                     "The employee is not in the data",
                     "Check the employee ID or upload the file again",
                     "Search again after the upload")

    att = calculate_attainment(row["actual_sales"], row["sales_target"])
    rate = get_commission_rate(att, plan)
    payout = calculate_payout(row["actual_sales"], rate)
    evidence = [f"Target: {row['sales_target']}", f"Actual sales: {row['actual_sales']}",
                f"Attainment: {att}%", f"Rate applied: {rate}", f"Payout: {payout}"]

    if att is None:
        root = "The target is zero, so attainment cannot be calculated"
        fix = "Correct the target in the data and recalculate"
    else:
        next_limit = None
        for limit in (plan["tier1_limit"], plan["tier2_limit"]):
            if att < limit:
                next_limit = limit
                break
        else:
            if att <= plan["tier3_limit"]:
                next_limit = plan["tier3_limit"]
        if next_limit is None:
            root = "Already in the top tier. The payout matches the plan."
            fix = "Explain the calculation to the employee"
        else:
            gap = round(next_limit - att, 2)
            root = (f"Attainment is {gap} points below the next tier boundary "
                    f"({next_limit}%). The payout matches the plan.")
            fix = "Share the calculation breakdown. Check if the plan tiers are set as intended."
    return _case(issue, checks, evidence, root, fix,
                 "Recalculate by hand: actual sales x rate")


def sales_missing(df):
    issue = "Sales are missing after the CSV upload"
    checks = ["Check required columns", "Check missing or invalid values",
              "Check duplicates and month format"]
    errors = validate_sales_data(df)
    if not errors:
        return _case(issue, checks, ["No validation errors found"],
                     "The file is valid. The data may not have been uploaded or refreshed.",
                     "Upload the file again and recalculate",
                     "Compare the row count in the file and in the dashboard")
    evidence = [f"Row {e['row']}: {e['message']}" for e in errors]
    if any(e["row"] == 0 for e in errors):
        root = "The file is missing required columns, so nothing could be imported"
    else:
        root = f"{len(errors)} issue(s) found. Rows with issues are left out of the calculation."
    return _case(issue, checks, evidence, root,
                 "Fix the listed rows in the CSV and upload it again",
                 "Upload again and check that the Validation tab shows no errors")


def attainment_wrong(df, employee_id, reported_pct):
    issue = f"{employee_id} says attainment shows {reported_pct}%"
    checks = ["Check target and actual values", "Recalculate attainment"]
    row = _find_row(df, employee_id)
    if row is None:
        return _case(issue, checks, [f"No record found for {employee_id}"],
                     "The employee is not in the data", "Check the employee ID",
                     "Search again")
    correct = calculate_attainment(row["actual_sales"], row["sales_target"])
    evidence = [f"Target: {row['sales_target']}", f"Actual sales: {row['actual_sales']}",
                f"Correct attainment: {correct}%", f"Reported attainment: {reported_pct}%"]
    if correct is not None and abs(correct - reported_pct) > 0.01:
        root = "The reported value does not match actual sales divided by target"
        fix = f"Show the corrected calculation: attainment is {correct}%"
    else:
        root = "The reported value matches the calculation"
        fix = "Explain the formula: actual sales / target x 100"
    return _case(issue, checks, evidence, root, fix,
                 "Recalculate by hand and compare")


def payout_not_updated(conn, df, employee_id, plan=None):
    plan = plan or DEFAULT_PLAN
    issue = f"{employee_id} says the payout was not updated"
    checks = ["Find the latest saved calculation", "Recalculate with the current plan",
              "Compare the two payouts"]
    row = _find_row(df, employee_id)
    latest = pd.read_sql_query(
        "SELECT payout, calculated_at FROM calculation_results "
        "WHERE employee_id = ? ORDER BY result_id DESC LIMIT 1",
        conn, params=(employee_id,))
    if row is None or latest.empty:
        return _case(issue, checks, ["No saved calculation found"],
                     "The payout was never calculated or saved",
                     "Run the calculation and save the results",
                     "Check calculation_results in the database")
    att = calculate_attainment(row["actual_sales"], row["sales_target"])
    expected = calculate_payout(row["actual_sales"], get_commission_rate(att, plan))
    saved = float(latest.iloc[0]["payout"])
    evidence = [f"Saved payout: {saved}", f"Saved at: {latest.iloc[0]['calculated_at']}",
                f"Payout with the current plan: {expected}"]
    if abs(saved - expected) > 0.01:
        root = "The saved result is out of date. The plan or data changed after it was saved."
        fix = "Recalculate and save the new result"
    else:
        root = "The saved payout matches the current plan"
        fix = "Ask the employee to refresh and check again"
    return _case(issue, checks, evidence, root, fix,
                 "Recalculate, then compare the saved payout with the expected payout")


def print_case(case):
    print("\n" + "=" * 60)
    print("Issue:", case["issue"])
    print("Checks:")
    for c in case["checks"]:
        print("  -", c)
    print("Evidence:")
    for e in case["evidence"]:
        print("  -", e)
    print("Root cause:", case["root_cause"])
    print("Resolution:", case["resolution"])
    print("Verification:", case["verification"])


if __name__ == "__main__":
    from modules.database import get_connection

    good = pd.read_csv("data/sales_data.csv")
    bad = pd.read_csv("data/bad_sales_data.csv")
    new_plan = dict(DEFAULT_PLAN, rate3=0.10)
    connection = get_connection()

    print_case(commission_too_low(good, "E002"))
    print_case(sales_missing(bad))
    print_case(attainment_wrong(good, "E001", 100))
    print_case(payout_not_updated(connection, good, "E001", new_plan))
    connection.close()