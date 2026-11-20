import pandas as pd

REQUIRED_COLUMNS = [
    "employee_id",
    "employee_name",
    "department",
    "sales_target",
    "actual_sales",
    "month",
]


def validate_sales_data(df):
    """Check a sales DataFrame. Returns a list of error dictionaries.

    Each error has: row, field, message.
    Row numbers match the CSV file (row 1 is the header, data starts at row 2).
    """
    errors = []

    # 1. Required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append({
            "row": 0,
            "field": "columns",
            "message": "Missing required columns: " + ", ".join(missing_cols),
        })
        return errors  # cannot check anything else without the columns

    for index, row in df.iterrows():
        row_number = index + 2

        # 2. Missing employee id or name
        if pd.isna(row["employee_id"]) or str(row["employee_id"]).strip() == "":
            errors.append({"row": row_number, "field": "employee_id",
                           "message": "Employee ID is missing"})
        if pd.isna(row["employee_name"]) or str(row["employee_name"]).strip() == "":
            errors.append({"row": row_number, "field": "employee_name",
                           "message": "Employee name is missing"})

        # 3. Sales values: must be present, numeric and not negative
        for field in ["sales_target", "actual_sales"]:
            value = pd.to_numeric(row[field], errors="coerce")
            if pd.isna(value):
                errors.append({"row": row_number, "field": field,
                               "message": f"{field} is missing or not a number"})
            elif value < 0:
                errors.append({"row": row_number, "field": field,
                               "message": f"{field} is negative ({value})"})
            elif field == "sales_target" and value == 0:
                errors.append({"row": row_number, "field": field,
                               "message": "sales_target is zero, attainment cannot be calculated"})

        # 4. Month format must be YYYY-MM
        month = pd.to_datetime(str(row["month"]), format="%Y-%m", errors="coerce")
        if pd.isna(month):
            errors.append({"row": row_number, "field": "month",
                           "message": f"Month '{row['month']}' is not in YYYY-MM format"})

    # 5. Duplicate employee id in the same month
    duplicates = df[df.duplicated(subset=["employee_id", "month"], keep=False)
                    & df["employee_id"].notna()]
    for index, row in duplicates.iterrows():
        errors.append({"row": index + 2, "field": "employee_id",
                       "message": f"Duplicate record for {row['employee_id']} in {row['month']}"})

    return sorted(errors, key=lambda e: e["row"])