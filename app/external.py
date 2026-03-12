import random
import time


# Simulated external credit bureau API
# In real world, this would be an HTTP call to a third-party service

class CreditBureauError(Exception):
    pass


def fetch_credit_score(applicant_id: str, pan_number: str, simulate_failure: bool = False) -> dict:
    """
    Simulates calling an external credit bureau API.
    - Randomly fails 20% of the time to demonstrate retry logic
    - Returns credit score, active loans, and payment history
    """
    time.sleep(0.3)  # simulate network latency

    # Simulate transient failures (20% chance)
    if simulate_failure or random.random() < 0.20:
        raise CreditBureauError("Credit bureau service temporarily unavailable (503)")

    # Deterministic score based on PAN for reproducible tests
    seed = sum(ord(c) for c in pan_number)
    random.seed(seed)

    credit_score = random.randint(550, 800)
    active_loans = random.randint(0, 4)
    missed_payments = random.randint(0, 5)
    total_existing_debt = random.randint(0, 1500000)

    random.seed()  # reset seed

    return {
        "source": "CreditBureau_Simulated",
        "applicant_id": applicant_id,
        "pan_number": pan_number,
        "credit_score": credit_score,
        "active_loans": active_loans,
        "missed_payments_last_12m": missed_payments,
        "total_existing_debt": total_existing_debt,
        "report_generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def fetch_credit_score_with_retry(applicant_id: str, pan_number: str, retries: int = 3, delay: float = 1.0) -> dict:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            result = fetch_credit_score(applicant_id, pan_number)
            result["attempts"] = attempt
            return result
        except CreditBureauError as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay)
    raise CreditBureauError(f"Credit bureau failed after {retries} attempts: {last_error}")
