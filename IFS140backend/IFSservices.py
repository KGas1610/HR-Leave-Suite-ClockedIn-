import sqlite3
from fastapi import HTTPException
from typing import List, Tuple, Optional, Any, Dict
from .IFSdb import get_conn
from .IFSsecurity import verify_password, hash_password

# Authenticate user details
def authenticate_user(emp_id: str, password: str) -> Optional[Tuple[str, str]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, password, salt, role FROM employees WHERE emp_id = ?", (emp_id,))
        row = cur.fetchone()

        if not row:
            return None

        name, stored_hash, salt, role = row
        if verify_password(password, stored_hash, salt):
            return (name, role)
    return None

# Get remaining leave balance
def get_leave_balance(emp_id: str) -> Optional[int]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT leave_available FROM employees WHERE emp_id = ?", (emp_id,))
        row = cur.fetchone()
        return row[0] if row else None

# Insert new leave request into the database
def submit_leave_request(emp_id: str, leave_type: str, description: str, days: int, paid_leave: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO leave_requests (emp_id, leave_type, description, days_requested, paid_leave, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
            """,
            (emp_id, leave_type, description, days, paid_leave),
        )
        conn.commit()
        return cur.rowcount > 0

# View leave requests for a specific employee
def view_leave_requests(emp_id: str) -> List[Tuple]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT request_id, leave_type, description, days_requested, paid_leave, status
            FROM leave_requests WHERE emp_id = ?
            """,
            (emp_id,),
        )
        return cur.fetchall()

# View all requests as a Manager/Admin
def view_all_leave_requests() -> List[Tuple]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT request_id, emp_id, leave_type, description, days_requested, paid_leave, status
            FROM leave_requests
            ORDER BY request_id DESC
            """
        )
        return cur.fetchall()

# Approve a leave request and deduct days from the employee's leave balance
def approve_leave_request(request_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT emp_id, days_requested, status FROM leave_requests WHERE request_id = ?",
            (request_id,),
        )
        row = cur.fetchone()
        if not row or row[2] == "Approved":
            return False

        emp_id, days_requested, _ = row
        cur.execute("SELECT leave_available FROM employees WHERE emp_id = ?", (emp_id,))
        emp_row = cur.fetchone()

        if not emp_row or emp_row[0] < days_requested:
            return False  # insufficient balance

        new_balance = emp_row[0] - days_requested
        cur.execute("UPDATE employees SET leave_available = ? WHERE emp_id = ?", (new_balance, emp_id))
        cur.execute("UPDATE leave_requests SET status = 'Approved' WHERE request_id = ?", (request_id,))
        conn.commit()
        return True

# Deny a leave request
def deny_leave_request(request_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE leave_requests SET status = 'Denied' WHERE request_id = ?", (request_id,))
        conn.commit()
        return cur.rowcount > 0


def view_all_staff() -> List[Tuple]:
    """List all employees and their current leave balances."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT emp_id, name, leave_available, role FROM employees")
        return cur.fetchall()

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

# Adds a new employee.
# Raises 409 if the employee ID already exists.
def add_employee(emp_id: str, name: str, password: str, leave: int, role: str):
    try:
        hashed, salt = hash_password(password)
        with get_conn() as conn:
            cursor = conn.cursor()

            # Check for duplicate ID
            cursor.execute("SELECT 1 FROM employees WHERE emp_id = ?", (emp_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail=f"Employee ID {emp_id} already exists.")

            cursor.execute("""
                INSERT INTO employees (emp_id, name, password, salt, leave_available, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (emp_id, name, hashed, salt, int(leave), role))
            conn.commit()

        return {
            "emp_id": emp_id,
            "name": name,
            "password": hashed,
            "leave_available": leave,
            "role": role,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not add employee: {e}")

def get_employee(emp_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM employees WHERE emp_id = ?", (emp_id,))
        row = cur.fetchone()
    return row_to_dict(row) if row else None

def list_employees() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM employees ORDER BY emp_id")
        rows = cur.fetchall()
    return [row_to_dict(r) for r in rows]

# Updating employee details; (name, password, leave, role)
def update_employee(emp_id: str, updates: dict):
    try:
        with get_conn() as conn:
            cursor = conn.cursor()

            # Check if employee exists
            cursor.execute("SELECT 1 FROM employees WHERE emp_id = ?", (emp_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Employee ID '{emp_id}' not found.")

            fields = []
            values = []

            if "name" in updates and updates["name"]:
                fields.append("name = ?")
                values.append(updates["name"])

            if "password" in updates and updates["password"]:
                hashed, salt = hash_password(updates["password"])
                fields.append("password = ?")
                fields.append("salt = ?")
                values.append(hashed)
                values.append(salt)

            if "leave_available" in updates:
                fields.append("leave_available = ?")
                values.append(int(updates["leave_available"]))

            if "role" in updates and updates["role"]:
                fields.append("role = ?")
                values.append(updates["role"])

            if not fields:
                raise HTTPException(status_code=400, detail="No valid fields provided for update.")

            values.append(emp_id)
            query = f"UPDATE employees SET {', '.join(fields)} WHERE emp_id = ?"
            cursor.execute(query, values)
            conn.commit()

        return {"status": "success", "message": f"Employee {emp_id} updated successfully."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not update employee: {e}")

# Removing employees 
def remove_employee(emp_id: str):
    try:
        with get_conn() as conn:
            cursor = conn.cursor()

            # Check if employee exists
            cursor.execute("SELECT 1 FROM employees WHERE emp_id = ?", (emp_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Employee ID '{emp_id}' not found.")

            cursor.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))
            conn.commit()

        return {"status": "success", "message": f"Employee {emp_id} removed successfully."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not remove employee: {e}")