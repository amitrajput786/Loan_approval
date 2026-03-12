import yaml
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config" / "workflow.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def evaluate_eligibility(data: dict, config: dict) -> dict:
    """Check basic eligibility rules. Returns pass/fail with trace."""
    rules = config["rules"]["eligibility"]
    triggered = []
    failed = []

    age = data.get("age", 0)
    if age < rules["min_age"]:
        failed.append(f"age {age} below minimum {rules['min_age']}")
    elif age > rules["max_age"]:
        failed.append(f"age {age} above maximum {rules['max_age']}")
    else:
        triggered.append(f"age_check: PASS (age={age})")

    income = data.get("annual_income", 0)
    if income < rules["min_annual_income"]:
        failed.append(f"annual_income {income} below minimum {rules['min_annual_income']}")
    else:
        triggered.append(f"income_check: PASS (income={income})")

    emp_months = data.get("employment_months", 0)
    if emp_months < rules["min_employment_months"]:
        failed.append(f"employment_months {emp_months} below minimum {rules['min_employment_months']}")
    else:
        triggered.append(f"employment_check: PASS (months={emp_months})")

    loan_amount = data.get("loan_amount", 0)
    loan_cfg = config["rules"]["loan"]
    if loan_amount < loan_cfg["min_amount"]:
        failed.append(f"loan_amount {loan_amount} below minimum {loan_cfg['min_amount']}")
    elif loan_amount > loan_cfg["max_amount"]:
        failed.append(f"loan_amount {loan_amount} above maximum {loan_cfg['max_amount']}")
    else:
        triggered.append(f"loan_amount_check: PASS (amount={loan_amount})")

    tenure = data.get("tenure_months", 0)
    if tenure < loan_cfg["min_tenure_months"] or tenure > loan_cfg["max_tenure_months"]:
        failed.append(f"tenure {tenure} out of range [{loan_cfg['min_tenure_months']}-{loan_cfg['max_tenure_months']}]")
    else:
        triggered.append(f"tenure_check: PASS (tenure={tenure})")

    passed = len(failed) == 0
    return {
        "passed": passed,
        "rules_triggered": triggered + [f"FAIL: {f}" for f in failed],
        "message": "Eligibility passed" if passed else f"Eligibility failed: {'; '.join(failed)}"
    }


def evaluate_risk(data: dict, credit_report: dict, config: dict) -> dict:
    """Assess risk using credit score, DTI, and LTI ratios."""
    risk_cfg = config["rules"]["risk"]
    triggered = []
    decision = "approve"

    credit_score = credit_report.get("credit_score", 0)
    cs_cfg = risk_cfg["credit_score"]
    if credit_score >= cs_cfg["approve_above"]:
        triggered.append(f"credit_score_check: APPROVE (score={credit_score} >= {cs_cfg['approve_above']})")
    elif credit_score >= cs_cfg["manual_review_above"]:
        triggered.append(f"credit_score_check: MANUAL_REVIEW (score={credit_score})")
        decision = "manual_review"
    else:
        triggered.append(f"credit_score_check: REJECT (score={credit_score} < {cs_cfg['reject_below']})")
        decision = "reject"

    # Debt-to-Income ratio
    annual_income = data.get("annual_income", 1)
    existing_debt = credit_report.get("total_existing_debt", 0)
    monthly_income = annual_income / 12
    loan_amount = data.get("loan_amount", 0)
    tenure = data.get("tenure_months", 1)
    monthly_emi = loan_amount / tenure
    dti = (existing_debt / 12 + monthly_emi) / monthly_income
    dti_cfg = risk_cfg["debt_to_income_ratio"]

    if dti <= dti_cfg["max_approve"]:
        triggered.append(f"dti_check: PASS (dti={dti:.2f})")
    elif dti <= dti_cfg["max_manual_review"]:
        triggered.append(f"dti_check: MANUAL_REVIEW (dti={dti:.2f})")
        if decision == "approve":
            decision = "manual_review"
    else:
        triggered.append(f"dti_check: REJECT (dti={dti:.2f} > {dti_cfg['max_manual_review']})")
        decision = "reject"

    # Loan-to-Income ratio
    lti = loan_amount / annual_income
    lti_cfg = risk_cfg["loan_to_income_ratio"]
    if lti <= lti_cfg["max_approve"]:
        triggered.append(f"lti_check: PASS (lti={lti:.2f})")
    elif lti <= lti_cfg["max_manual_review"]:
        triggered.append(f"lti_check: MANUAL_REVIEW (lti={lti:.2f})")
        if decision == "approve":
            decision = "manual_review"
    else:
        triggered.append(f"lti_check: REJECT (lti={lti:.2f})")
        decision = "reject"

    missed = credit_report.get("missed_payments_last_12m", 0)
    if missed > 3:
        triggered.append(f"payment_history_check: REJECT (missed_payments={missed})")
        decision = "reject"
    else:
        triggered.append(f"payment_history_check: PASS (missed_payments={missed})")

    messages = {
        "approve": "Risk assessment passed — application approved",
        "manual_review": "Risk assessment flagged — requires manual review",
        "reject": "Risk assessment failed — application rejected"
    }

    return {
        "decision": decision,
        "rules_triggered": triggered,
        "message": messages[decision],
        "computed": {"credit_score": credit_score, "dti": round(dti, 4), "lti": round(lti, 4)}
    }
