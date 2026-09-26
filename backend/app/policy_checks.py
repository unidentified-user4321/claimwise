from decimal import Decimal


def run_policy_checks(context: dict) -> dict:

    claim = context["claim"]
    policy = context["policy"]
    vehicle = context["vehicle"]

    issues = []

    
    # Policy status
    

    policy_active = policy.policy_status.lower() == "active"

    if not policy_active:
        issues.append("Policy is not active.")

    
    # Incident inside policy period
    

    incident_within_policy_period = None
    if policy.policy_end_date is None:
        issues.append("Policy end date is unavailable; coverage period could not be determined.")
    else:
        incident_within_policy_period = (
            policy.policy_bind_date
            <= claim.incident_date
            <= policy.policy_end_date
        )

    if incident_within_policy_period is False:
        issues.append(
            "Incident date falls outside the policy coverage period."
        )

    
    # Claim amount vs coverage limit
    

    claim_amount = Decimal(claim.total_claim_amount)
    coverage_limit = Decimal(policy.coverage_limit) if policy.coverage_limit is not None else None

    within_coverage_limit = None
    if coverage_limit is None:
        issues.append("Policy coverage limit is unavailable; amount check could not be determined.")
    else:
        within_coverage_limit = claim_amount <= coverage_limit

    if within_coverage_limit is False:
        issues.append(
            "Claim amount exceeds the policy coverage limit."
        )

    
    # Deductible
    
    deductible = Decimal(policy.deductible)

    amount_after_deductible = max(
        Decimal("0"),
        claim_amount - deductible,
    )

   
    # Vehicle-policy relationship
   

    vehicle_matches_policy = (
        vehicle.policy_id == policy.policy_id
        and vehicle.customer_id == claim.customer_id
    )

    if not vehicle_matches_policy:
        issues.append(
            "Vehicle does not match the claim policy/customer."
        )

   
    # Result
   

    return {
        "policy_active": policy_active,
        "incident_within_policy_period": incident_within_policy_period,
        "within_coverage_limit": within_coverage_limit,
        "vehicle_matches_policy": vehicle_matches_policy,

        "claim_amount": float(claim_amount),
        "coverage_limit": float(coverage_limit) if coverage_limit is not None else None,
        "deductible": float(deductible),
        "amount_after_deductible": float(amount_after_deductible),

        "issues": issues,
    }
