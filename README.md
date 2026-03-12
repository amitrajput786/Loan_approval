# 🏦 Loan Approval Workflow System

A configurable workflow decision platform for processing loan applications with full auditability, idempotency, retry logic, and rule-based decision making.

---

## 🚀 Quick Start (run in under 2 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn app.main:app --reload --port 8000

# 3. Open browser
http://localhost:8000        ← Home page
http://localhost:8000/docs  ← Swagger UI (interactive API)
```

---

## 🧪 Run Tests

```bash
pytest tests/ -v
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/apply` | Submit a loan application |
| GET | `/applications` | List all applications |
| GET | `/applications/{id}` | Get application by ID |
| GET | `/applications/{id}/audit` | Full audit trail |
| GET | `/health` | Health check |

---

## 📋 Example Request

```bash
curl -X POST http://localhost:8000/apply \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ-001",
    "applicant_name": "Ravi Kumar",
    "age": 30,
    "pan_number": "ABCDE1234F",
    "annual_income": 800000,
    "employment_months": 24,
    "loan_amount": 500000,
    "tenure_months": 60,
    "purpose": "home_renovation"
  }'
```

---

## ⚙️ Configuration

All rules are in `config/workflow.yaml` — **no code changes needed** to update thresholds:

```yaml
rules:
  eligibility:
    min_age: 18
    min_annual_income: 200000
  risk:
    credit_score:
      approve_above: 700
      manual_review_above: 600
```

---

## 🏗️ Architecture

```
Request → Schema Validation → Eligibility Rules → Credit Bureau (external, retry)
       → Risk Assessment → Final Decision → Audit Log
```

### Components

| File | Responsibility |
|------|---------------|
| `app/main.py` | FastAPI REST layer |
| `app/workflow.py` | Workflow orchestrator |
| `app/engine.py` | Rule evaluator (reads YAML) |
| `app/external.py` | Simulated credit bureau with retries |
| `app/models.py` | SQLite state + audit persistence |
| `config/workflow.yaml` | All rules and thresholds |

### Key Design Decisions

- **SQLite** — zero-setup persistence with full ACID guarantees
- **YAML config** — rules/thresholds changeable without code changes
- **Idempotency** — `request_id` deduplication at intake
- **Retry logic** — credit bureau retried up to 3 times with delay
- **Audit trail** — every stage logged with rules triggered and data snapshot
- **State history** — full lifecycle tracked with timestamps

### Scaling Considerations

- Replace SQLite with PostgreSQL for multi-instance deployments
- Add Redis for distributed idempotency key storage
- Credit bureau calls can be made async with Celery/RQ
- Rule engine can load configs from DB for hot-reload without restart
