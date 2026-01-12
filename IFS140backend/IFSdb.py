import sqlite3
from pathlib import Path
from .IFSsecurity import hash_password
from typing import Dict

DB_FILE = "test1.db"

# Path created to the database 
def ensure_parent():
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)

# class Role:
#     MANAGER = "Manager"
#     ADMIN = "Admin"
#     STAFF = "Staff"

# Sample employee data to seed the database
employees_data: Dict[str, dict] = {
    "MAN01": {"name": "Patrick", "password": "SuchIsLife", "leave_available": 45, "role": "Manager"},
    "KGAS01": {"name": "Kaleb", "password": "451", "leave_available": 27, "role": "Admin"},
    "MBAT02": {"name": "Mbasa", "password": "454", "leave_available": 32, "role": "Frontend Dev"},
    "IKOL03": {"name": "Inga", "password": "451", "leave_available": 14, "role": "Chief Consultant"},
    "TMOK04": {"name": "Tshwaraganang", "password": "456", "leave_available": 30, "role": "System Analyst"},
    "AKRI05": {"name": "Ayron", "password": "455", "leave_available": 23, "role": "Backend Dev"},
    "SMAT06": {"name": "Sekwele", "password": "454", "leave_available": 10, "role": "Data Analyst"},
}

def setup_database():
    ensure_parent()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            salt TEXT NOT NULL,
            leave_available INTEGER NOT NULL DEFAULT 0,
            role TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            description TEXT,
            days_requested INTEGER NOT NULL,
            paid_leave INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
        """)
        # seed the data into the database for testing
        for emp_id, details in employees_data.items():
            plain = str(details.get("password", ""))
            hashed, salt = hash_password(plain)
            cursor.execute(
                """
                INSERT OR REPLACE INTO employees
                (emp_id, name, password, salt, leave_available, role)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (emp_id, details["name"], hashed, salt, int(details.get("leave_available", 0)), details.get("role", "Staff")),
            )
        conn.commit()

# Easy to use connect fuction for our backend functions
def get_conn():
    return sqlite3.connect(str(DB_FILE))

