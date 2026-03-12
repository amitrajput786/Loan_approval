# 🏦 LoanFlow — Intelligent Loan Approval Workflow System

> A configurable, auditable, and explainable workflow decision platform for loan applications — built with Python, FastAPI, and Matplotlib.

![Status](https://img.shields.io/badge/status-production--ready-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📸 Screenshots

### Application Form UI
![Main UI](https://github.com/amitrajput786/Loan_approval/blob/main/uploads/Main_ui.png?raw=true)

> Submit a loan application, see real-time decision with rules triggered, credit score, DTI and LTI metrics — all in one screen.

---

### Visual Audit Report — Risk Analysis Charts (Python · Matplotlib)
![Audit Graphs](https://github.com/amitrajput786/Loan_approval/blob/main/uploads/Audit_graphs.png?raw=true)

> Server-side generated charts: Risk Gauge Dashboard, Applicant Financial Radar, Rules Outcome Donut, Workflow Execution Timeline, and Rule-by-Rule Evaluation Bar Chart.

---

### Stage-by-Stage Audit Trail
![Audit Trail](https://github.com/amitrajput786/Loan_approval/blob/main/uploads/audit2.png?raw=true)

> Every workflow stage logged with exact rules triggered, values compared, timestamps, and expandable raw data snapshots.

---

### State Transition History
![State History](https://github.com/amitrajput786/Loan_approval/blob/main/uploads/audits1.png?raw=true)

> Full lifecycle tracking — every status change from `pending → processing → eligibility_check → credit_check → risk_assessment → final_decision` with reason and timestamp.

---

## 📌 What Problem Does This Solve?

Traditional loan approval systems are **black boxes** — applicants get a yes or no with no explanation, banks cannot trace *why* a decision was made, and changing a rule requires a full code redeployment.

**LoanFlow solves 5 real problems:**

| Problem | How LoanFlow Solves It |
|---|---|
| ❓ "Why was my loan rejected?" | Every rule that ran is logged with exact values — full explainability |
| 🔁 Duplicate submissions | Idempotency key (`request_id`) — same input always returns same output |
| 💥 Credit bureau goes down | Auto-retry 3 times with delay, falls back to manual review gracefully |
| 🛠️ Changing rules needs redeployment | All thresholds in `workflow.yaml` — edit and restart, zero code changes |
| 📊 Auditors can't understand decisions | Python Matplotlib charts visualise every metric and rule outcome |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn app.main:app --reload --port 8000

# 3. Open browser
http://localhost:8000        ← Application Form UI
http://localhost:8000/docs   ← Swagger Interactive API Docs
```

---

## 🧪 Run Tests

```bash
pytest tests/ -v
```

13 tests — all passing. Covers happy path, rejections, idempotency, retry flow, invalid input, audit trail, and rule trace verification.

---

## 🗂️ Project Structure

```
loan-workflow/
├── app/
│   ├── main.py          # FastAPI REST API — routes only
│   ├── workflow.py      # Pipeline orchestrator — runs all 5 stages
│   ├── engine.py        # Rule evaluator — reads from YAML config
│   ├── external.py      # Simulated credit bureau — retry + failure handling
│   ├── models.py        # SQLite — applications, audit log, state history
│   └── charts.py        # Matplotlib chart generator — 5 visual risk charts
├── config/
│   └── workflow.yaml    # ALL rules and thresholds live here
├── static/
│   ├── index.html       # Loan application form UI
│   └── audit.html       # Visual audit report with charts
├── tests/
│   └── test_workflow.py # 13 tests covering all scenarios
├── requirements.txt
└── README.md
```

---

## 🧠 Decision Model — How Loan Approval Works

Every application passes through a **5-stage sequential pipeline**:

```
[1] Schema Validation
        ↓ PASS
[2] Eligibility Check  ── FAIL ──→  REJECTED
        ↓ PASS
[3] Credit Bureau Call ── FAIL ──→  MANUAL REVIEW  (after 3 retries)
        ↓ PASS
[4] Risk Assessment    ── FLAG ──→  MANUAL REVIEW
        ↓ PASS
[5] Final Decision     ──────────→  APPROVED
```

### Stage 2 — Eligibility Rules (Hard Cutoffs)

| Rule | Threshold |
|---|---|
| Minimum Age | 18 years |
| Maximum Age | 75 years |
| Minimum Annual Income | ₹2,00,000 |
| Minimum Employment | 6 months |
| Loan Amount | ₹10,000 – ₹50,00,000 |
| Tenure | 6 – 360 months |

### Stage 3 — Credit Bureau (External Dependency)

Fetches credit score, active loans, missed payments (12m), and total existing debt from a simulated external API.

**Failure handling:** Retries 3 times with 1-second delay. After all retries fail → routed to manual review. Never crashes, never loses data.

### Stage 4 — Risk Assessment (Core Decision Engine)

#### Credit Score
| Score | Decision |
|---|---|
| ≥ 700 | ✅ Approve |
| 600 – 699 | 🔍 Manual Review |
| < 600 | ❌ Reject |

#### Debt-to-Income Ratio (DTI)
```
DTI = (Existing Monthly Debt + New EMI) / Monthly Income
```
| DTI | Decision |
|---|---|
| ≤ 40% | ✅ Approve |
| 40% – 55% | 🔍 Manual Review |
| > 55% | ❌ Reject |

#### Loan-to-Income Ratio (LTI)
```
LTI = Loan Amount / Annual Income
```
| LTI | Decision |
|---|---|
| ≤ 5x | ✅ Approve |
| 5x – 8x | 🔍 Manual Review |
| > 8x | ❌ Reject |

#### Payment History
| Missed Payments (12 months) | Decision |
|---|---|
| ≤ 3 | ✅ Pass |
| > 3 | ❌ Reject |

**Final logic:** Any rejection rule → Rejected. Any manual review flag (no rejection) → Manual Review. All pass → Approved.

---

## ⚙️ Configuration — Change Rules Without Code

Edit `config/workflow.yaml` and restart. No code deployment needed:

```yaml
rules:
  eligibility:
    min_age: 18
    min_annual_income: 200000

  risk:
    credit_score:
      approve_above: 700
      manual_review_above: 600

    debt_to_income_ratio:
      max_approve: 0.40
      max_manual_review: 0.55

  loan:
    max_amount: 5000000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application form UI |
| GET | `/audit?id={id}` | Visual audit report with charts |
| POST | `/apply` | Submit a loan application |
| GET | `/applications` | List all applications |
| GET | `/applications/{id}` | Get application by ID |
| GET | `/applications/{id}/audit` | Full audit trail (JSON) |
| GET | `/applications/{id}/charts` | Matplotlib charts as base64 |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

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

### Example Response

```json
{
  "application_id": "04d93761-e6e0-4de6-8b29-5aa6c2b3b570",
  "status": "manual_review",
  "message": "Risk assessment flagged — requires manual review",
  "rules_triggered": [
    "credit_score_check: APPROVE (score=728 >= 700)",
    "dti_check: MANUAL_REVIEW (dti=0.47)",
    "lti_check: PASS (lti=0.62)",
    "payment_history_check: PASS (missed_payments=0)"
  ],
  "computed_metrics": {
    "credit_score": 728,
    "dti": 0.4744,
    "lti": 0.625
  },
  "audit_url": "/applications/04d93761.../audit"
}
```

---

## 🏗️ Architecture

```
Request → Schema Validation → Eligibility Rules → Credit Bureau (retry)
       → Risk Assessment → Final Decision → Audit Log
```

### Component Responsibilities

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI REST layer — routes only |
| `app/workflow.py` | Pipeline orchestrator — 5 stages in sequence |
| `app/engine.py` | Rule evaluator — reads thresholds from YAML |
| `app/external.py` | Simulated credit bureau with retry logic |
| `app/models.py` | SQLite — state, audit trail, history |
| `app/charts.py` | Matplotlib — generates 5 risk analysis charts |
| `config/workflow.yaml` | All rules and thresholds |

### Key Design Decisions

- **SQLite** — zero-setup persistence with full ACID guarantees
- **YAML config** — rules changeable without code changes
- **Idempotency** — `request_id` deduplication at intake
- **Retry logic** — credit bureau retried 3 times with configurable delay
- **Audit trail** — every stage logged with rules triggered and data snapshot
- **Matplotlib charts** — server-side Python charts embedded as base64 in audit page

### Scaling Considerations

- Replace SQLite with PostgreSQL for multi-instance deployments
- Add Redis for distributed idempotency key storage
- Credit bureau calls can be made async with Celery/RQ
- Rule engine can load configs from DB for hot-reload without restart
- Charts can be cached in Redis to avoid regeneration on every request

---

## 🤝 What Makes This Different

1. **Explainability by design** — every decision includes the exact rules triggered with actual values, not just a score
2. **Visual audit reports** — Python generates 5 Matplotlib charts automatically on every audit page load
3. **Config-driven rules** — business thresholds editable outside of code, no redeployment needed
4. **Resilient by default** — external failures never crash the system, always route to manual review
5. **Full lifecycle tracking** — complete state history with timestamps from intake to final decision

---

*Built for Hackathon — Configurable Workflow Decision Platform*
