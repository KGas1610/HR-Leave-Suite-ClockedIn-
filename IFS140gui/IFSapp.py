import customtkinter as ctk
from tkinter import messagebox, Listbox, END, SINGLE, Scrollbar, RIGHT, Y
import requests
import random

API_URL = "http://127.0.0.1:8000"

greetings = ["Hello", "Sawubona", "Molo", "Dumela", "Hallo", "Thobela", "Lufuno", "Mhoro", "Avuxeni"]

# GUI CLASS 
class IFSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClockedIn HR Suite")
        self.root.geometry("600x450")
        ctk.set_window_scaling(1.5)
        ctk.set_widget_scaling(1.5)
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("green")

        self.API_URL = API_URL
        self.user_data = {}
        self.show_login()

    # WINDOW HELPERS 
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def api_post(self, endpoint, data=None):
        data = data or {}
        try:
            url = f"{self.API_URL}{endpoint}"
            response = requests.post(url, json=data)

            try:
                json_data = response.json()
            except ValueError:
                json_data = {"detail": f"Invalid response: {response.text}"}

            json_data["status_code"] = response.status_code
            return json_data

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not reach server:\n{e}")
            return {"detail": str(e), "status_code": 0}

    def api_get(self, endpoint):
        try:
            res = requests.get(f"{API_URL}{endpoint}")
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not reach server:\n{e}")
            return None

    def api_delete(self, endpoint):
        try:
            url = f"{self.API_URL}{endpoint}"
            response = requests.delete(url)
            try:
                data = response.json()
            except ValueError:
                data = {"detail": response.text}
            data["status_code"] = response.status_code
            return data
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return {"detail": str(e), "status_code": 0}
        
    # LOGIN SCREEN
    def show_login(self):
        self.clear_window()
        
        frame = ctk.CTkFrame(self.root, corner_radius=15)
        frame.pack(pady=60, padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text=f"{random.choice(greetings)}", font=("Lucida Grande", 22, "bold"),
                     text_color="#27823f").pack(pady=(15, 5))
        ctk.CTkLabel(frame, text="Welcome to ClockedIn HR Suite", font=("Lucida Grande", 16),
                     text_color="grey").pack(pady=(0, 20))

        ctk.CTkLabel(frame, text="Employee ID:", text_color="#27823f").pack(anchor="w", padx=20)
        self.emp_entry = ctk.CTkEntry(frame, placeholder_text="Enter ID eg. TEST01", text_color="#27823f")
        self.emp_entry.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame, text="Password:", text_color="#27823f").pack(anchor="w", padx=20)
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="Enter Password", show="*", text_color="#27823f")
        self.pass_entry.pack(fill="x", padx=20, pady=5)
        self.show_password_switch = ctk.CTkSwitch(frame, text="Show Password", text_color="#27823f", cursor="hand2",
                                                  font=("Lucida Grande", 11), command=self.toggle_password)
        self.show_password_switch.pack(anchor="w", padx=20, pady=5)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text="Login", fg_color="#27823f", text_color="white",
                      cursor="hand2", width=120, command=self.login_user).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", text_color="white",
                      cursor="hand2", width=120, command=self.root.destroy).pack(side="left", padx=10)

    def toggle_password(self):
            if self.show_password_switch.get() == 1:
                self.pass_entry.configure(show="")   
            else:
                self.pass_entry.configure(show="*")
    
    def login_user(self):
        emp_id = self.emp_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not emp_id or not password:
            messagebox.showwarning("Missing Info", "Please enter both ID and password.")
            return

        res = self.api_post("/login", {"emp_id": emp_id, "password": password})
        if not res or res.get("status") != "success":
            messagebox.showerror("Login Failed", "Invalid ID or password.")
            return

        self.user_data = res
        role = res.get("role")
        if role in ("Admin", "Manager"):
            self.show_admin_dashboard()
        else:
            self.show_staff_dashboard()

    # STAFF DASHBOARD
    def show_staff_dashboard(self):
        self.clear_window()
        name = self.user_data.get("name", "User")
        emp_id = self.user_data.get("emp_id")
        days = self.user_data.get("leave_available", 0)

        ctk.CTkLabel(
            self.root,
            text=f"Welcome {name}! ({emp_id})",
            font=("Lucida Grande", 18, "bold"),
            text_color="#27823f",
        ).pack(pady=15)

        ctk.CTkLabel(
            self.root,
            text=f"Leave Days Available: {days}",
            font=("Lucida Grande", 14), 
            text_color="#27823f"
        ).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(self.root, corner_radius=10)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Request Leave", command=self.show_leave_form).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="View My Requests", command=self.show_my_requests).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Logout", command=self.show_login).grid(row=1, column=0, columnspan=2, pady=15)

    def show_leave_form(self):
        self.clear_window()
        ctk.CTkLabel(self.root, text="Submit Leave Request", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=20)

        frame = ctk.CTkFrame(self.root)
        frame.pack(pady=10, padx=20, fill="both")

        self.leave_type = ctk.CTkEntry(frame, placeholder_text="Leave Type")
        self.leave_desc = ctk.CTkEntry(frame, placeholder_text="Description (optional)")
        self.leave_days = ctk.CTkEntry(frame, placeholder_text="Days Requested")
        self.leave_paid = ctk.CTkSwitch(frame, text="Paid Leave")

        for w in (self.leave_type, self.leave_desc, self.leave_days, self.leave_paid):
            w.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(frame, text="Submit", command=self.submit_leave).pack(pady=20)
        ctk.CTkButton(frame, text="Back", command=self.show_staff_dashboard).pack()

    def submit_leave(self):
        emp_id = self.user_data.get("emp_id")
        data = {
            "emp_id": emp_id,
            "leave_type": self.leave_type.get().strip(),
            "description": self.leave_desc.get().strip(),
            "days": int(self.leave_days.get() or 0),
            "paid_leave": 1 if self.leave_paid.get() else 0,
        }
        res = self.api_post("/leave/submit", data)
        if res and res.get("status") == "success":
            messagebox.showinfo("Success", "Leave request submitted.")
            self.show_staff_dashboard()

    def show_my_requests(self):
        emp_id = self.user_data.get("emp_id")
        res = self.api_get(f"/leave/view/{emp_id}")
        self.clear_window()
        ctk.CTkLabel(self.root, text="My Leave Requests", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=20)

        frame = ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        for r in res.get("requests", []):
            req_id, ltype, desc, days, paid, status = r
            ctk.CTkLabel(
                frame,
                text=f"#{req_id} | {ltype} | {days} days | {'Paid' if paid else 'Unpaid'} | {status}\n{desc or ''}",
                anchor="w",
                justify="left",
            ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(self.root, text="Back", command=self.show_staff_dashboard).pack(pady=10)

    # ADMIN/MANAGER DASHBOARD
    def show_admin_dashboard(self):
        self.clear_window()
        name = self.user_data.get("name", "Admin")
        days = self.user_data.get("leave_available", 0)
        frame = ctk.CTkFrame(self.root, corner_radius=15)
        frame.pack(pady=60, padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text=f"Welcome {name}", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=15)
        ctk.CTkLabel(frame, text=f"Leave days available: {days}", text_color="gray").pack()
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="View All Requests", command=self.manage_leave_requests).grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="View All Staff", command=self.show_all_staff).grid(row=1, column=1, columnspan=2, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Add Employee", command=self.show_add_employee_form).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Remove Employee", command=self.show_remove_employee_form).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Update Employee", command=self.show_update_employee_form).grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Logout", fg_color="#27823f", command=self.show_login).grid(row=2, column=0, columnspan=3, pady=10)
        
    def manage_leave_requests(self):
        res = self.api_get("/leave/view_all")
        self.clear_window()
        ctk.CTkLabel(self.root, text="Manage Leave Requests", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=20)

        frame = ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        for r in res.get("requests", []):
            req_id, emp_id, ltype, desc, days, paid, status = r
            text = f"#{req_id} | {emp_id} | {ltype} | {days} days | {'Paid' if paid else 'Unpaid'} | {status}\n{desc or ''}"

            item_frame = ctk.CTkFrame(frame)
            item_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(item_frame, text=text, anchor="w", justify="left").pack(side="left", padx=5)
            if status == "Pending":
                ctk.CTkButton(item_frame, text="Approve", width=70, command=lambda r=req_id: self.approve_request(r)).pack(side="right", padx=2)
                ctk.CTkButton(item_frame, text="Deny", width=70, command=lambda r=req_id: self.deny_request(r)).pack(side="right", padx=2)

        ctk.CTkButton(self.root, text="Back", command=self.show_admin_dashboard).pack(pady=10)

    def approve_request(self, request_id):
        res = self.api_post(f"/leave/approve/{request_id}")
        if res and res.get("status") == "success":
            messagebox.showinfo("Success", "Request approved.")
            self.manage_leave_requests()

    def deny_request(self, request_id):
        res = self.api_post(f"/leave/deny/{request_id}")
        if res and res.get("status") == "success":
            messagebox.showinfo("Success", "Request denied.")
            self.manage_leave_requests()

    def show_all_staff(self):
        res = self.api_get("/staff/all")
        self.clear_window()
        ctk.CTkLabel(self.root, text="All Staff Members", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=20)

        frame = ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        for e in res.get("employees", []):
            emp_id, name, leave_avail, role = e
            ctk.CTkLabel(
                frame,
                text=f"{emp_id} | {name} | {leave_avail} days left | {role}",
                anchor="w",
                justify="left",
            ).pack(fill="x", padx=10, pady=3)

        ctk.CTkButton(self.root, text="Back", command=self.show_admin_dashboard).pack(pady=10)

    def show_add_employee_form(self):
        self.clear_window()
        ctk.CTkLabel(
            self.root,
            text="Add New Employee",
            font=("Lucida Grande", 18, "bold"),
            text_color="#27823f"
        ).pack(pady=20)

        frame = ctk.CTkFrame(self.root)
        frame.pack(pady=10, padx=20, fill="both")

        self.new_emp_id = ctk.CTkEntry(frame, placeholder_text="Employee ID (e.g, TEST01)")
        self.new_emp_name = ctk.CTkEntry(frame, placeholder_text="Name")
        self.new_emp_password = ctk.CTkEntry(frame, placeholder_text="Password", show="*")
        self.new_emp_role = ctk.CTkEntry(frame, placeholder_text="Role")
        self.new_emp_leave = ctk.CTkEntry(frame, placeholder_text="Leave Available")

        for w in (self.new_emp_id, self.new_emp_name, self.new_emp_password, self.new_emp_role, self.new_emp_leave):
            w.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(frame, text="Submit", command=self.submit_add_employee).pack(pady=20)
        ctk.CTkButton(frame, text="Back", command=self.show_admin_dashboard).pack()


    def submit_add_employee(self):
        emp_id = self.new_emp_id.get().strip()
        name = self.new_emp_name.get().strip()
        password = self.new_emp_password.get().strip()
        role = self.new_emp_role.get().strip()
        leave_text = self.new_emp_leave.get().strip()

        if not (emp_id and name and password and role):
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        try:
            leave_available = int(leave_text) if leave_text else 0
        except ValueError:
            messagebox.showerror("Error", "Leave Available must be a number.")
            return

        data = {
            "emp_id": emp_id,
            "name": name,
            "password": password,
            "role": role,
            "leave_available": leave_available,
        }

        res = self.api_post("/employees/add", data)
        if not res:
            messagebox.showerror("Error", "No response from server.")
            return

        status = res.get("status_code", 0)

        if status in (200, 201) and res.get("emp_id"):
            messagebox.showinfo("Success", f"Employee {res['name']} ({res['emp_id']}) added successfully.")
            self.show_admin_dashboard()

        elif status == 409:
            messagebox.showwarning("Duplicate", res.get("detail", "Employee ID already exists."))

        elif status == 422:
            messagebox.showerror("Validation Error", res.get("detail", "Invalid input data."))

        else:
            messagebox.showerror("Error", res.get("detail", "An unknown error occurred."))


        
    def show_update_employee_form(self):
        self.clear_window()
        ctk.CTkLabel(self.root, text="Update Employee", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=20)

        frame = ctk.CTkFrame(self.root)
        frame.pack(pady=10, padx=20, fill="both")

        self.update_emp_id = ctk.CTkEntry(frame, placeholder_text="Employee ID")
        self.update_emp_name = ctk.CTkEntry(frame, placeholder_text="New Name (leave blank to skip)")
        self.update_emp_password = ctk.CTkEntry(frame, placeholder_text="New Password (leave blank to skip)", show="*")
        self.update_emp_role = ctk.CTkEntry(frame, placeholder_text="New Role (leave blank to skip)")
        self.update_emp_leave = ctk.CTkEntry(frame, placeholder_text="New Leave Available (leave blank to skip)")

        for w in (self.update_emp_id, self.update_emp_name, self.update_emp_password, self.update_emp_role, self.update_emp_leave):
            w.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(frame, text="Submit", command=self.submit_update_employee).pack(pady=20)
        ctk.CTkButton(frame, text="Back", command=self.show_admin_dashboard).pack()
    
    def submit_update_employee(self):
        emp_id = self.update_emp_id.get().strip()
        if not emp_id:
            messagebox.showerror("Error", "Employee ID is required.")
            return

        data = {
            "name": self.update_emp_name.get().strip() or None,
            "password": self.update_emp_password.get().strip() or None,
            "role": self.update_emp_role.get().strip() or None,
            "leave_available": int(self.update_emp_leave.get().strip()) if self.update_emp_leave.get().strip() else None,
        }

        res = requests.put(f"{self.API_URL}/employees/{emp_id}", json=data)
        try:
            result = res.json()
        except ValueError:
            result = {"detail": res.text}

        if res.status_code == 200 and result.get("status") == "success":
            messagebox.showinfo("Success", result["message"])
            self.show_admin_dashboard()
        else:
            messagebox.showerror("Error", result.get("detail", "Failed to update employee."))
    
    def show_remove_employee_form(self):
        self.clear_window()
        ctk.CTkLabel(self.root, text="Remove Employee", font=("Lucida Grande", 18, "bold"), text_color="#27823f").pack(pady=20)

        frame = ctk.CTkFrame(self.root)
        frame.pack(pady=10, padx=20, fill="both")

        self.remove_emp_id = ctk.CTkEntry(frame, placeholder_text="Employee ID to Remove")
        self.remove_emp_id.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(frame, text="Submit", command=self.submit_remove_employee).pack(pady=20)
        ctk.CTkButton(frame, text="Back", command=self.show_admin_dashboard).pack()
    
    def submit_remove_employee(self):
        emp_id = self.remove_emp_id.get().strip()
        if not emp_id:
            messagebox.showerror("Error", "Please enter an Employee ID.")
            return

        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete employee {emp_id}?")
        if not confirm:
            return

        res = self.api_delete(f"/employees/{emp_id}")
        if res["status_code"] == 200 and res.get("status") == "success":
            messagebox.showinfo("Deleted", res["message"])
            self.show_admin_dashboard()
        else:
            messagebox.showerror("Error", res.get("detail", "Failed to delete employee."))

# RUN APP
if __name__ == "__main__":
    root = ctk.CTk()
    app = IFSApp(root)
    root.mainloop()
