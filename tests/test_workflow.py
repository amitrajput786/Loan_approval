import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models import init_db

client = TestClient(app)


def fresh_id():
    return f"REQ-{uuid.uuid4().hex[:8].upper()}"


BASE_PAYLOAD = {
    "applicant_name": "Ravi Kumar",
    "age": 30,
    "pan_number": "ABCDE1234F",
    "annual_income": 800000,
    "employment_months": 24,
    "loan_amount": 500000,
    "tenure_months": 60,
    "purpose": "home_renovation"
}


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


# ---- 1. HEALTH CHECK ----
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- 2. HAPPY PATH — VALID APPLICATION GOES THROUGH FULL PIPELINE ----
def test_happy_path_approval():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id()}
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Must reach a final decision stage (not stuck in processing)
    assert data["status"] in ["approved", "manual_review", "rejected"]
    assert "application_id" in data
    assert "rules_triggered" in data
    assert len(data["rules_triggered"]) > 0
    # Audit trail must be recorded
    audit = client.get(f"/applications/{data['application_id']}/audit")
    assert audit.status_code == 200
    assert len(audit.json()["audit_trail"]) >= 2


# ---- 3. REJECTION — UNDERAGE ----
def test_reject_underage():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id(), "age": 16}
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert any("age" in rule for rule in r.json()["rules_triggered"])


# ---- 4. REJECTION — LOW INCOME ----
def test_reject_low_income():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id(), "annual_income": 50000}
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


# ---- 5. REJECTION — LOAN TOO SMALL ----
def test_reject_loan_too_small():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id(), "loan_amount": 100}
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


# ---- 6. REJECTION — LOAN TOO LARGE ----
def test_reject_loan_too_large():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id(), "loan_amount": 99999999}
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


# ---- 7. IDEMPOTENCY — SAME REQUEST ID ----
def test_idempotency():
    req_id = fresh_id()
    payload = {**BASE_PAYLOAD, "request_id": req_id}
    r1 = client.post("/apply", json=payload)
    r2 = client.post("/apply", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["idempotent"] == True
    assert r1.json()["application_id"] == r2.json()["application_id"]


# ---- 8. INVALID SCHEMA ----
def test_invalid_schema_missing_field():
    payload = {"request_id": fresh_id(), "applicant_name": "Test"}  # missing required fields
    r = client.post("/apply", json=payload)
    assert r.status_code == 422


# ---- 9. AUDIT TRAIL ----
def test_audit_trail_exists():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id()}
    r = client.post("/apply", json=payload)
    app_id = r.json()["application_id"]
    audit = client.get(f"/applications/{app_id}/audit")
    assert audit.status_code == 200
    data = audit.json()
    assert len(data["audit_trail"]) >= 2
    assert len(data["state_history"]) >= 2
    stages = [entry["stage"] for entry in data["audit_trail"]]
    assert "intake" in stages


# ---- 10. APPLICATION NOT FOUND ----
def test_application_not_found():
    r = client.get("/applications/nonexistent-id-xyz")
    assert r.status_code == 404


# ---- 11. LIST APPLICATIONS ----
def test_list_applications():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id()}
    client.post("/apply", json=payload)
    r = client.get("/applications")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ---- 12. SHORT EMPLOYMENT REJECTION ----
def test_reject_short_employment():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id(), "employment_months": 2}
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


# ---- 13. RULE TRACE IN RESPONSE ----
def test_rules_are_traced():
    payload = {**BASE_PAYLOAD, "request_id": fresh_id()}
    r = client.post("/apply", json=payload)
    data = r.json()
    assert isinstance(data["rules_triggered"], list)
    assert len(data["rules_triggered"]) > 0