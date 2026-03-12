from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import json

from app.models import init_db, get_application_by_id, list_applications
from app.workflow import process_application, get_full_audit
from app.charts import generate_all_charts

BASE_DIR = Path(__file__).parent.parent

app = FastAPI(
    title="Loan Approval Workflow System",
    description="Configurable workflow decision platform for loan applications",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


# ---------- SCHEMAS ----------

class LoanApplicationRequest(BaseModel):
    request_id: str = Field(..., description="Unique idempotency key")
    applicant_name: str
    age: int = Field(..., ge=1, le=120)
    pan_number: str = Field(..., min_length=10, max_length=10)
    annual_income: float = Field(..., gt=0)
    employment_months: int = Field(..., ge=0)
    loan_amount: float = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0)
    purpose: Optional[str] = "personal"


# ---------- ROUTES ----------

@app.get("/", response_class=FileResponse)
def root():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/audit", response_class=FileResponse)
def audit_page():
    return FileResponse(BASE_DIR / "static" / "audit.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "loan-workflow"}


@app.post("/apply")
def apply_for_loan(request: LoanApplicationRequest):
    """Submit a loan application. Idempotent — same request_id returns same result."""
    data = request.model_dump()
    return process_application(request.request_id, data)


@app.get("/applications")
def get_applications(status: Optional[str] = None):
    """List all applications, optionally filtered by status."""
    apps = list_applications(status)
    for a in apps:
        a["data"] = json.loads(a["data"])
    return {"total": len(apps), "applications": apps}


@app.get("/applications/{app_id}")
def get_application(app_id: str):
    app = get_application_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app["data"] = json.loads(app["data"])
    return app


@app.get("/applications/{app_id}/audit")
def get_audit(app_id: str):
    """Full audit trail + state history."""
    if not get_application_by_id(app_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return get_full_audit(app_id)


@app.get("/applications/{app_id}/charts")
def get_charts(app_id: str):
    """Generate matplotlib charts for this application as base64 PNG images."""
    app_row = get_application_by_id(app_id)
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")
    app_data = json.loads(app_row["data"])
    audit_data = get_full_audit(app_id)
    charts = generate_all_charts(audit_data, app_data)
    return charts