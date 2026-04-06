"""
ISO 27001 Compliance Mapping
============================
Maps IAM risks to ISO 27001 controls.

ISO 27001 Controls Relevant to IAM:
- A.9.2: User access management
- A.9.4: System and application access control
- A.9.5: Access to networks and network services
- A.12.6: Technical vulnerability management

This module provides conceptual mapping - full ISO 27001 compliance
requires comprehensive security management system implementation.
"""
import logging
from typing import Dict, Any, List, Optional
from ..graph.escalation import detect_privilege_escalation, detect_wildcard_permissions
from ..ml.predict import calculate_risk_score

logger = logging.getLogger(__name__)

# ISO 27001 Control Mappings
ISO27001_CONTROLS = {
    "A.9.2.1": {
        "name": "User registration and de-registration",
        "description": "Formal user registration and de-registration process",
        "iam_relevance": "Roles should be properly provisioned and deprovisioned"
    },
    "A.9.2.2": {
        "name": "User access provisioning",
        "description": "Formal user access provisioning process",
        "iam_relevance": "IAM roles should follow least-privilege principle"
    },
    "A.9.2.3": {
        "name": "Management of privileged access rights",
        "description": "Privileged access rights should be restricted and controlled",
        "iam_relevance": "Escalation permissions should be minimized"
    },
    "A.9.2.4": {
        "name": "Management of secret authentication information",
        "description": "Secret authentication information should be managed securely",
        "iam_relevance": "IAM credentials and keys should be rotated"
    },
    "A.9.4.1": {
        "name": "Information access restriction",
        "description": "Access to information and application system functions should be restricted",
        "iam_relevance": "IAM policies should restrict access to required resources only"
    },
    "A.9.4.2": {
        "name": "Secure log-on procedures",
        "description": "Where required by the access control policy, access to systems and applications should be controlled by a secure log-on procedure",
        "iam_relevance": "IAM roles should use secure authentication"
    },
    "A.9.4.3": {
        "name": "Password management system",
        "description": "Password management systems should be interactive and should ensure quality passwords",
        "iam_relevance": "IAM password policies should be enforced"
    },
    "A.9.4.4": {
        "name": "Use of privileged utility programs",
        "description": "Access to privileged utility programs should be restricted and controlled",
        "iam_relevance": "IAM roles with administrative permissions should be restricted"
    },
    "A.9.4.5": {
        "name": "Access control to program source code",
        "description": "Access to program source code should be restricted",
        "iam_relevance": "IAM roles should not have unnecessary code access"
    },
    "A.12.6.1": {
        "name": "Management of technical vulnerabilities",
        "description": "Information about technical vulnerabilities should be obtained in a timely fashion",
        "iam_relevance": "IAM misconfigurations should be identified and remediated"
    }
}


def map_iam_risks_to_iso27001(
    role_name: Optional[str] = None,
    cloud: Optional[str] = None
) -> Dict[str, Any]:
    """
    Map IAM risks to ISO 27001 controls.
    
    Args:
        role_name: Optional specific role to analyze
        cloud: Optional cloud filter
        
    Returns:
        Dictionary with ISO 27001 compliance mapping
    """
    logger.info(f"Mapping IAM risks to ISO 27001 for role: {role_name or 'all'}")
    
    # Detect escalation risks
    escalation_risks = detect_privilege_escalation(cloud=cloud)
    wildcard_risks = detect_wildcard_permissions(cloud=cloud)
    
    if role_name:
        escalation_risks = [r for r in escalation_risks if r["role"] == role_name]
        wildcard_risks = [r for r in wildcard_risks if r["role"] == role_name]
    
    # Map to ISO 27001 controls
    compliance_gaps = []
    
    # A.9.2.3: Management of privileged access rights
    if escalation_risks:
        compliance_gaps.append({
            "control": "A.9.2.3",
            "control_name": ISO27001_CONTROLS["A.9.2.3"]["name"],
            "status": "NON-COMPLIANT",
            "finding": f"{len(escalation_risks)} roles have privilege escalation permissions",
            "affected_roles": [r["role"] for r in escalation_risks],
            "recommendation": "Remove or restrict escalation permissions following least-privilege"
        })
    
    # A.9.4.1: Information access restriction
    if wildcard_risks:
        compliance_gaps.append({
            "control": "A.9.4.1",
            "control_name": ISO27001_CONTROLS["A.9.4.1"]["name"],
            "status": "NON-COMPLIANT",
            "finding": f"{len(wildcard_risks)} roles have wildcard permissions",
            "affected_roles": [r["role"] for r in wildcard_risks],
            "recommendation": "Replace wildcard permissions with specific resource permissions"
        })
    
    # Calculate overall compliance score
    total_controls = len(ISO27001_CONTROLS)
    non_compliant = len(compliance_gaps)
    compliance_score = ((total_controls - non_compliant) / total_controls * 100) if total_controls > 0 else 0
    
    return {
        "standard": "ISO 27001",
        "scope": "IAM Access Control",
        "compliance_score": round(compliance_score, 2),
        "total_controls_assessed": total_controls,
        "non_compliant_controls": non_compliant,
        "compliance_gaps": compliance_gaps,
        "controls": ISO27001_CONTROLS,
        "assessment_date": None  # Would be set to current date in production
    }


def generate_iso27001_report(cloud: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive ISO 27001 compliance report.
    
    Args:
        cloud: Optional cloud filter
        
    Returns:
        Complete compliance report
    """
    mapping = map_iam_risks_to_iso27001(cloud=cloud)
    
    # Add risk scores
    from ..ml.predict import batch_calculate_risk_scores
    risk_scores = batch_calculate_risk_scores(cloud=cloud)
    high_risk_roles = [r for r in risk_scores if r.get("risk_score", 0) > 70]
    
    mapping["high_risk_roles"] = len(high_risk_roles)
    mapping["risk_summary"] = {
        "high": len([r for r in risk_scores if r.get("risk_level") == "high"]),
        "medium": len([r for r in risk_scores if r.get("risk_level") == "medium"]),
        "low": len([r for r in risk_scores if r.get("risk_level") == "low"])
    }
    
    return mapping


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== ISO 27001 COMPLIANCE MAPPING ===")
    report = generate_iso27001_report()
    
    print(f"\nCompliance Score: {report['compliance_score']}%")
    print(f"Non-Compliant Controls: {report['non_compliant_controls']}")
    print("\nCompliance Gaps:")
    for gap in report["compliance_gaps"]:
        print(f"  - {gap['control']}: {gap['control_name']}")
        print(f"    Finding: {gap['finding']}")
