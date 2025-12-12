"""
FHIR data minimizer - removes verbose fields while maintaining FHIR structure.
"""

from typing import Dict, Any, List, Optional


def minimize_fhir_bundle(fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimize FHIR bundle by removing verbose fields while keeping structure.
    
    Args:
        fhir_bundle: Full FHIR bundle dictionary
        
    Returns:
        Minimized FHIR bundle with same structure
    """
    if not fhir_bundle or not isinstance(fhir_bundle, dict):
        return fhir_bundle
    
    minimized = {
        "resourceType": fhir_bundle.get("resourceType", "Bundle"),
        "type": fhir_bundle.get("type"),
        "total": fhir_bundle.get("total"),
        "entry": []
    }
    
    # Minimize each entry
    entries = fhir_bundle.get("entry", [])
    for entry in entries:
        if "resource" in entry:
            minimized_resource = minimize_resource(entry["resource"])
            minimized_entry = {
                "fullUrl": entry.get("fullUrl"),
                "resource": minimized_resource
            }
            minimized["entry"].append(minimized_entry)
    
    return minimized


def minimize_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimize a single FHIR resource.
    
    Removes:
    - meta (except lastUpdated if important)
    - extension
    - text
    - implicitRules
    - language
    - Multiple coding entries (keeps primary)
    
    Keeps:
    - resourceType
    - id
    - Core fields (status, code, value, date, etc.)
    - Essential references
    """
    if not resource or not isinstance(resource, dict):
        return resource
    
    minimized = {
        "resourceType": resource.get("resourceType"),
        "id": resource.get("id")
    }
    
    # Keep status fields
    if "status" in resource:
        minimized["status"] = resource["status"]
    if "clinicalStatus" in resource:
        minimized["clinicalStatus"] = simplify_coding(resource["clinicalStatus"])
    if "verificationStatus" in resource:
        minimized["verificationStatus"] = simplify_coding(resource["verificationStatus"])
    
    # Keep code (simplified)
    if "code" in resource:
        minimized["code"] = simplify_coding(resource["code"])
    
    # Keep value fields
    if "valueQuantity" in resource:
        minimized["valueQuantity"] = resource["valueQuantity"]
    if "valueString" in resource:
        minimized["valueString"] = resource["valueString"]
    if "valueCodeableConcept" in resource:
        minimized["valueCodeableConcept"] = simplify_coding(resource["valueCodeableConcept"])
    
    # Keep dates
    for date_field in ["effectiveDateTime", "onsetDateTime", "recordedDate", "date", "period"]:
        if date_field in resource:
            minimized[date_field] = resource[date_field]
    
    # Keep essential references
    for ref_field in ["subject", "patient", "encounter", "performer", "recorder"]:
        if ref_field in resource:
            ref = resource[ref_field]
            if isinstance(ref, dict):
                minimized[ref_field] = {
                    "reference": ref.get("reference"),
                    "display": ref.get("display")
                }
    
    # Keep medication-specific fields
    if resource.get("resourceType") == "MedicationStatement":
        if "medicationCodeableConcept" in resource:
            minimized["medicationCodeableConcept"] = simplify_coding(resource["medicationCodeableConcept"])
        if "dosage" in resource:
            minimized["dosage"] = resource["dosage"][:1] if isinstance(resource["dosage"], list) else resource["dosage"]
    
    # Keep condition-specific fields
    if resource.get("resourceType") == "Condition":
        if "severity" in resource:
            minimized["severity"] = simplify_coding(resource["severity"])
        if "bodySite" in resource:
            minimized["bodySite"] = simplify_coding(resource["bodySite"])
    
    # Keep observation-specific fields
    if resource.get("resourceType") == "Observation":
        if "interpretation" in resource:
            minimized["interpretation"] = simplify_coding(resource["interpretation"])
        if "component" in resource:
            minimized["component"] = resource["component"][:3]  # Limit components
    
    # Keep patient-specific fields
    if resource.get("resourceType") == "Patient":
        if "name" in resource:
            minimized["name"] = resource["name"][:1] if isinstance(resource["name"], list) else resource["name"]
        if "birthDate" in resource:
            minimized["birthDate"] = resource["birthDate"]
        if "gender" in resource:
            minimized["gender"] = resource["gender"]
    
    return minimized


def simplify_coding(coding_obj: Any) -> Any:
    """
    Simplify coding objects - keep only primary coding entry.
    
    Args:
        coding_obj: Can be CodeableConcept, Coding, or dict with coding array
        
    Returns:
        Simplified coding structure
    """
    if not coding_obj:
        return coding_obj
    
    if isinstance(coding_obj, dict):
        # If it has a coding array, take the first one
        if "coding" in coding_obj:
            codings = coding_obj["coding"]
            if isinstance(codings, list) and len(codings) > 0:
                primary = codings[0]
                return {
                    "coding": [{
                        "system": primary.get("system"),
                        "code": primary.get("code"),
                        "display": primary.get("display")
                    }],
                    "text": coding_obj.get("text")
                }
            else:
                return coding_obj
        # If it's already a single coding
        elif "system" in coding_obj or "code" in coding_obj:
            return {
                "system": coding_obj.get("system"),
                "code": coding_obj.get("code"),
                "display": coding_obj.get("display")
            }
    
    return coding_obj



