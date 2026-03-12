from app.models import (
    create_application, get_application_by_request_id,
    update_status, add_audit, get_audit_trail, get_state_history
)
from app.engine import load_config, evaluate_eligibility, evaluate_risk
from app.external import fetch_credit_score_with_retry, CreditBureauError
import json


def process_application(request_id: str, data: dict) -> dict:
    config = load_config()

    existing = get_application_by_request_id(request_id)
    if existing:
        return {
            "idempotent": True,
            "message": "Duplicate request — returning existing result",
            "application_id": existing["id"],
            "status": existing["status"],
            "data": json.loads(existing["data"])
        }

    app = create_application(request_id, data)
    app_id = app["id"]
    update_status(app_id, "processing", "Workflow started")
    add_audit(app_id, "intake", "success", ["schema_validated"], "Application received and validated", data)

    update_status(app_id, "eligibility_check", "Running eligibility rules")
    eligibility = evaluate_eligibility(data, config)
    add_audit(app_id, "eligibility_check", "pass" if eligibility["passed"] else "fail",
              eligibility["rules_triggered"], eligibility["message"], data)

    if not eligibility["passed"]:
        update_status(app_id, "rejected", eligibility["message"])
        return _build_response(app_id, "rejected", eligibility["message"], eligibility["rules_triggered"])

    update_status(app_id, "credit_check", "Calling credit bureau")
    retry_cfg = next(s for s in config["stages"] if s["name"] == "credit_check")
    try:
        credit_report = fetch_credit_score_with_retry(
            applicant_id=app_id,
            pan_number=data.get("pan_number", "ABCDE1234F"),
            retries=retry_cfg["retries"],
            delay=retry_cfg["retry_delay_seconds"]
        )
        add_audit(app_id, "credit_check", "success",
                  [f"credit_bureau_call: SUCCESS (attempts={credit_report['attempts']}, score={credit_report['credit_score']})"],
                  "Credit report fetched successfully", credit_report)
    except CreditBureauError as e:
        add_audit(app_id, "credit_check", "fail", ["credit_bureau_call: FAILED after retries"], str(e), {})
        update_status(app_id, "manual_review", f"Credit bureau unavailable: {e}")
        return _build_response(app_id, "manual_review", str(e), ["credit_bureau_unreachable"])

    update_status(app_id, "risk_assessment", "Evaluating risk rules")
    risk = evaluate_risk(data, credit_report, config)
    add_audit(app_id, "risk_assessment", risk["decision"],
              risk["rules_triggered"], risk["message"], risk["computed"])

    status_map = {"approve": "approved", "reject": "rejected", "manual_review": "manual_review"}
    final = status_map.get(risk["decision"], "manual_review")
    update_status(app_id, final, risk["message"])
    add_audit(app_id, "final_decision", final, [f"final_status: {final}"], risk["message"])

    return _build_response(app_id, final, risk["message"], risk["rules_triggered"], risk.get("computed"))


def _build_response(app_id, status, message, rules, computed=None):
    return {
        "idempotent": False,
        "application_id": app_id,
        "status": status,
        "message": message,
        "rules_triggered": rules,
        "computed_metrics": computed or {},
        "audit_url": f"/applications/{app_id}/audit"
    }


def get_full_audit(app_id: str) -> dict:
    return {
        "application_id": app_id,
        "state_history": get_state_history(app_id),
        "audit_trail": get_audit_trail(app_id)
    }