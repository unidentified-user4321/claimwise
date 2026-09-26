import pandas as pd


def build_fraud_features(claim, customer, policy, vehicle, derived):
    """
    Convert application/database data into the exact feature structure
    expected by the fraud detection model.
    """

    incident_date = claim.incident_date

    features = {
        # Customer / policy
        # "months_as_customer": derived.months_as_customer,
        # "age": derived.age,
        "months_as_customer": derived["months_as_customer"],
        "age": derived["age"],

        "policy_state": policy.policy_state,
        "policy_csl": policy.policy_csl,
        "policy_deductable": float(policy.deductible),
        "policy_annual_premium": float(policy.annual_premium),
        "umbrella_limit": float(policy.umbrella_limit),

        "insured_sex": customer.sex,
        "insured_education_level": customer.education_level,
        "insured_occupation": customer.occupation,
        "insured_hobbies": customer.hobbies,
        "insured_relationship": customer.relationship,

        # Current incident
        "incident_type": claim.incident_type,
        "collision_type": claim.collision_type or "Unknown",
        "incident_severity": claim.incident_severity,
        "authorities_contacted": claim.authorities_contacted or "Unknown",
        "incident_state": claim.incident_state,
        "incident_city": claim.incident_city,
        "incident_hour_of_the_day": claim.incident_hour_of_the_day,

        "number_of_vehicles_involved": claim.number_of_vehicles_involved,
        "property_damage": (
            "YES" if claim.property_damage is True
            else "NO" if claim.property_damage is False
            else "Unknown"
        ),
        "bodily_injuries": claim.bodily_injuries,
        "witnesses": claim.witnesses,

        "police_report_available": (
            "YES" if claim.police_report_available is True
            else "NO" if claim.police_report_available is False
            else "Unknown"
        ),

        "total_claim_amount": float(claim.total_claim_amount),

        # Vehicle
        "auto_make": vehicle.make,
        "auto_model": vehicle.model,
        "auto_year": vehicle.year,

        # Derived from incident date
        "incident_month": incident_date.month,
        "incident_day_of_week": incident_date.weekday(),
    }

    return pd.DataFrame([features])