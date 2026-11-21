CREATE TABLE IF NOT EXISTS employees (
    employee_id   TEXT PRIMARY KEY,
    employee_name TEXT NOT NULL,
    department    TEXT
);

CREATE TABLE IF NOT EXISTS sales_records (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id   TEXT NOT NULL,
    month         TEXT NOT NULL,
    sales_target  REAL NOT NULL,
    actual_sales  REAL NOT NULL,
    UNIQUE (employee_id, month),
    FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

CREATE TABLE IF NOT EXISTS commission_plans (
    plan_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name    TEXT,
    tier1_limit  REAL,
    tier2_limit  REAL,
    tier3_limit  REAL,
    rate1        REAL,
    rate2        REAL,
    rate3        REAL,
    rate4        REAL,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calculation_results (
    result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id     TEXT NOT NULL,
    month           TEXT NOT NULL,
    plan_id         INTEGER,
    attainment_pct  REAL,
    commission_rate REAL,
    payout          REAL,
    calculated_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    FOREIGN KEY (plan_id) REFERENCES commission_plans (plan_id)
);