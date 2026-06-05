import sqlite3
import csv
import json
from datetime import datetime
from config import SQL_DB_PATH, EMPLOYEES_CSV_PATH


def init_relational_db():
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT,
            medical_balance INTEGER,
            casual_balance INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            req_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            leave_type TEXT,
            start_date TEXT,
            total_days INTEGER,
            timestamp TEXT,
            FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
        )
    """)

    # Check if data exists before importing
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        try:
            with open(EMPLOYEES_CSV_PATH, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    cursor.execute(
                        "INSERT OR IGNORE INTO employees VALUES (?, ?, ?, ?)",
                        (
                            row["emp_id"],
                            row["name"],
                            int(row["medical_balance"]),
                            int(row["casual_balance"]),
                        ),
                    )
        except FileNotFoundError:
            print(f"Warning: {EMPLOYEES_CSV_PATH} not found. Skipping data import.")

    conn.commit()
    conn.close()


def submit_leave_request(
    employee_id: str, leave_type: str, start_date: str, total_days: int
) -> str:
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()
    leave_type = leave_type.lower()
    balance_column = f"{leave_type}_balance"

    cursor.execute(
        f"SELECT {balance_column} FROM employees WHERE emp_id = ?", (employee_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return json.dumps({"status": "error", "message": "Employee ID not found."})

    current_balance = result[0]
    if total_days > current_balance:
        conn.close()
        return json.dumps(
            {
                "status": "error",
                "message": f"Insufficient {leave_type} balance. Available: {current_balance}, Requested: {total_days}",
            }
        )

    try:
        new_balance = current_balance - total_days
        cursor.execute(
            f"UPDATE employees SET {balance_column} = ? WHERE emp_id = ?",
            (new_balance, employee_id),
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO leave_requests (emp_id, leave_type, start_date, total_days, timestamp) VALUES (?, ?, ?, ?, ?)",
            (employee_id, leave_type, start_date, total_days, timestamp),
        )
        conn.commit()
        return json.dumps(
            {
                "status": "success",
                "message": f"{leave_type.capitalize()} leave approved.",
                "new_balance": new_balance,
            }
        )
    except sqlite3.Error as e:
        conn.rollback()
        return json.dumps({"status": "error", "message": f"Database error: {str(e)}"})
    finally:
        conn.close()
