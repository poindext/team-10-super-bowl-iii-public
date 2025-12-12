"""
Utility functions to extract health summary information from FHIR data.
"""

from typing import Dict, Any, Optional


def extract_health_summary(fhir_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract key health information from FHIR data for quick summary display.
    
    Args:
        fhir_data: FHIR bundle dictionary
        
    Returns:
        Dictionary with:
        - one_line_summary: Brief health summary
        - diagnoses: List of active diagnoses
        - medication_count: Number of medications
        - last_encounter_date: Most recent encounter date
    """
    if not fhir_data or not isinstance(fhir_data, dict):
        return {
            "one_line_summary": "No health data available",
            "diagnoses": [],
            "medication_count": 0,
            "last_encounter_date": None
        }
    
    entries = fhir_data.get("entry", [])
    resources = [entry.get("resource", {}) for entry in entries if "resource" in entry]
    
    # Extract conditions (diagnoses)
    active_conditions = []
    all_conditions = []
    
    for resource in resources:
        if resource.get("resourceType") == "Condition":
            all_conditions.append(resource)
            # Check if condition is active
            clinical_status = resource.get("clinicalStatus", {})
            if isinstance(clinical_status, dict):
                coding = clinical_status.get("coding", [])
                if coding and any(c.get("code") == "active" for c in coding):
                    # Extract condition name
                    code = resource.get("code", {})
                    if isinstance(code, dict):
                        code_coding = code.get("coding", [])
                        if code_coding:
                            display = code_coding[0].get("display", "Unknown condition")
                            active_conditions.append(display)
    
    # Count medications
    medication_count = sum(1 for r in resources if r.get("resourceType") == "MedicationStatement")
    
    # Find most recent encounter
    last_encounter_date = None
    encounters = [r for r in resources if r.get("resourceType") == "Encounter"]
    if encounters:
        dates = []
        for enc in encounters:
            period = enc.get("period", {})
            if isinstance(period, dict):
                start = period.get("start")
                if start:
                    dates.append(start)
        if dates:
            last_encounter_date = max(dates)
    
    # Generate one-line summary
    if active_conditions:
        if len(active_conditions) == 1:
            summary = f"Active condition: {active_conditions[0]}"
        elif len(active_conditions) == 2:
            summary = f"Active conditions: {active_conditions[0]} and {active_conditions[1]}"
        else:
            summary = f"{len(active_conditions)} active conditions, including {active_conditions[0]}"
    elif all_conditions:
        summary = f"{len(all_conditions)} condition(s) on record"
    elif medication_count > 0:
        summary = f"{medication_count} medication(s) on record"
    elif encounters:
        summary = "Health record available with encounter history"
    else:
        summary = "Limited health data available"
    
    return {
        "one_line_summary": summary,
        "diagnoses": active_conditions[:10],  # Limit to 10 for display
        "medication_count": medication_count,
        "last_encounter_date": last_encounter_date,
        "total_conditions": len(all_conditions),
        "active_conditions_count": len(active_conditions)
    }

