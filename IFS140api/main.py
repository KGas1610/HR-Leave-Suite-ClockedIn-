from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from IFS140backend.IFSdb import setup_database
from IFS140backend import IFSservices as services

app = FastAPI(title="IFS140 Leave Management API")

# Models for our responses and requests
class LoginRequest(BaseModel):
    emp_id: str
    password: str

class LeaveRequest(BaseModel):
    emp_id: str
    leave_type: str
    description: str
    days: int
    paid_leave: int

class EmployeeBase(BaseModel):
    name: str = Field(..., example="Kaleb")
    password: str = Field(..., example="4515449")
    leave_available: int = Field(..., example=20)
    role: str = Field(..., example="Staff")

class EmployeeCreate(EmployeeBase):
    emp_id: str = Field(..., example="KGAS01")

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    leave_available: Optional[int] = None
    role: Optional[str] = None

class EmployeeOut(EmployeeBase):
    emp_id: str

# API Startup
@app.on_event("startup")
def startup_event():
    setup_database()

# Authentication
@app.post("/login")
def login(data: LoginRequest):
    user = services.authenticate_user(data.emp_id, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    name, role = user
    return {"status": "success", "emp_id": data.emp_id, "name": name, "role": role, "leave_available": services.get_leave_balance(data.emp_id)}

# Leave Requests
@app.post("/leave/submit")
def submit_leave(data: LeaveRequest):
    ok = services.submit_leave_request(data.emp_id, data.leave_type, data.description, data.days, data.paid_leave)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to submit leave request")
    return {"status": "success", "message": "Leave request submitted"}

@app.get("/leave/view/{emp_id}")
def view_my_requests(emp_id: str):
    requests = services.view_leave_requests(emp_id)
    return {"status": "success", "requests": requests}

@app.get("/leave/view_all")
def view_all():
    return {"status": "success", "requests": services.view_all_leave_requests()}

@app.post("/leave/approve/{request_id}")
def approve(request_id: int):
    ok = services.approve_leave_request(request_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to approve request")
    return {"status": "success", "message": "Request approved"}

@app.post("/leave/deny/{request_id}")
def deny(request_id: int):
    ok = services.deny_leave_request(request_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to deny request")
    return {"status": "success", "message": "Request denied"}

# Staff Managment
@app.get("/staff/all")
def view_staff():
    return {"status": "success", "employees": services.view_all_staff()}

@app.get("/staff", response_model=List[EmployeeOut])
def api_list_employees():
    return services.list_employees()

@app.get("/staff/{emp_id}", response_model=EmployeeOut)
def api_get_employee(emp_id: int):
    emp = services.get_employee(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@app.post("/staff", response_model=EmployeeOut, status_code=201)
def api_add_employee(payload: EmployeeCreate):
    created = services.add_employee(
        emp_id=payload.emp_id,
        name=payload.name,
        password=payload.password,
        leave=payload.leave_available,
        role=payload.role
    )
    return created

@app.post("/employees/add", response_model=EmployeeOut, status_code=201)
def legacy_add_employee(payload: EmployeeCreate):
    return api_add_employee(payload)

@app.put("/staff/{emp_id}", response_model=EmployeeOut)
def api_update_employee(emp_id: int, payload: EmployeeUpdate):
    updated = services.update_employee(emp_id, payload.name, payload.password, payload.leave_available, payload.role)
    if not updated:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated

@app.delete("/employees/{emp_id}")
def api_delete_employee(emp_id: str):
    return services.remove_employee(emp_id)

@app.put("/employees/{emp_id}")
def api_update_employee(emp_id: str, payload: EmployeeUpdate):
    updates = payload.dict(exclude_unset=True)
    return services.update_employee(emp_id, updates)