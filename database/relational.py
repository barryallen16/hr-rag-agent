import csv
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from config import EMPLOYEES_CSV_PATH, SQL_DB_PATH

LEAVE_TYPES = {"medical", "casual"}


@contextmanager
def _conn():
    conn = sqlite3.connect(SQL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_relational_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                emp_id TEXT PRIMARY KEY,
                name TEXT,
                medical_balance INTEGER,
                casual_balance INTEGER
            );
            CREATE TABLE IF NOT EXISTS leave_requests (
                req_id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id TEXT,
                leave_type TEXT,
                start_date TEXT,
                total_days INTEGER,
                timestamp TEXT,
                FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
            );
        """)
        if conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
            try:
                with open(EMPLOYEES_CSV_PATH, newline="") as f:
                    for row in csv.DictReader(f):
                        conn.execute(
                            "INSERT OR IGNORE INTO employees VALUES (?,?,?,?)",
                            (row["emp_id"], row["name"],
                             int(row["medical_balance"]), int(row["casual_balance"])),
                        )
            except FileNotFoundError:
                print(f"Warning: {EMPLOYEES_CSV_PATH} not found. Skipping data import.")


def _validate_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def submit_leave_request(employee_id, leave_type, start_date, total_days):
    leave_type = (leave_type or "").lower()
    if leave_type not in LEAVE_TYPES:
        return json.dumps({"status": "error", "message": f"Unknown leave type: {leave_type}"})
    if not _validate_date(start_date):
        return json.dumps({"status": "error", "message": "start_date must be YYYY-MM-DD"})
    if not isinstance(total_days, int) or total_days <= 0:
        return json.dumps({"status": "error", "message": "total_days must be a positive int"})
    col = f"{leave_type}_balance"
    with _conn() as conn:
        row = conn.execute(f"SELECT {col} FROM employees WHERE emp_id=?", (employee_id,)).fetchone()
        if not row:
            return json.dumps({"status": "error", "message": "Employee ID not found."})
        bal = row[0]
        if total_days > bal:
            return json.dumps({"status": "error", "message": f"Insufficient {leave_type} balance. Available: {bal}, Requested: {total_days}"})
        conn.execute(f"UPDATE employees SET {col}=? WHERE emp_id=?", (bal - total_days, employee_id))
        conn.execute(
            "INSERT INTO leave_requests (emp_id, leave_type, start_date, total_days, timestamp) VALUES (?,?,?,?,?)",
            (employee_id, leave_type, start_date, total_days, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return json.dumps({"status": "success", "message": f"{leave_type.capitalize()} leave approved.", "new_balance": bal - total_days})