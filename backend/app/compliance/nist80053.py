"""
NIST SP 800-53 Compliance Mapping
===================================
Maps IAM risks to NIST SP 800-53 controls.

NIST SP 800-53 Controls Relevant to IAM:
- AC-2: Account Management
- AC-3: Access Enforcement
- AC-5: Separation of Duties
- AC-6: Least Privilege
- AC-7: Unsuccessful Logon Attempts
- IA-1: Identification and Authentication Policy
- IA-2: Identification and Authentication (Organizational Users)

This module provides conceptual mapping - full NIST 800-53 compliance
requires comprehensive security control implementation.
"""
import logging
from typing import Dict, Any, List, Optional
from ..graph.escalation import detect_privilege_escalation, detect_wildcard_permissions
from ..ml.predict import calculate_risk_score

logger = logging.getLogger(__name__)

# NIST SP 800-53 Control Mappings
NIST80053_CONTROLS = {
    "AC-2": {
        "name": "Account Management",
        "description": "Manage system accounts, including establishing, activating, modifying, disabling, and removing accounts",
        "iam_relevance": "IAM roles should be properly managed throughout lifecycle"
    },
    "AC-2(1)": {
        "name": "Account Management | Automated System Account Management",
        "description": "Employ automated mechanisms to support the management of system accounts",
        "iam_relevance": "IAM role provisioning should be automated"
    },
    "AC-3": {
        "name": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access to information and system resources",
        "iam_relevance": "IAM policies should enforce access controls"
    },
    "AC-5": {
        "name": "Separation of Duties",
        "description": "Separate duties of individuals to reduce risk of malevolent activity",
        "iam_relevance": "IAM roles should not combine conflicting permissions"
    },
    "AC-6": {
        "name": "Least Privilege",
        "description": "Employ the principle of least privilege, allowing only authorized accesses",
        "iam_relevance": "IAM roles should follow least-privilege principle - critical control"
    },
    "AC-6(1)": {
        "name": "Least Privilege | Authorize Access to Security Functions",
        "description": "Authorize access to security functions and security-relevant information",
        "iam_relevance": "IAM administrative roles should be restricted"
    },
    "AC-6(2)": {
        "name": "Least Privilege | Non-Privileged Access for Non-Security Functions",
        "description": "Require that users of system accounts with non-privileged access use non-privileged accounts",
        "iam_relevance": "IAM roles should not have unnecessary privileges"
    },
    "AC-7": {
        "name": "Unsuccessful Logon Attempts",
        "description": "Enforce a limit on the number of unsuccessful logon attempts",
        "iam_relevance": "IAM authentication should limit failed attempts"
    },
    "IA-1": {
        "name": "Identification and Authentication Policy",
        "description": "Develop, document, and disseminate identification and authentication policy",
        "iam_relevance": "IAM authentication policies should be documented"
    },
    "IA-2": {
        "name": "Identification and Authentication (Organizational Users)",
        "description": "Uniquely identify and authenticate organizational users",
        "iam_relevance": "IAM roles should use strong authentication"
    },
    "IA-4": {
        "name": "Identifier Management",
        "description": "Manage system identifiers by uniquely identifying users and devices",
        "iam_relevance": "IAM role identifiers should be unique and managed"
    },
    "AC-17": {
        "name": "Remote Access",
        "description": "Control and monitor remote access methods",
        "iam_relevance": "IAM roles used for remote access should be restricted"
    }
}


def map_iam_risks_to_nist80053(
    role_name: Optional[str] = None,
    cloud: Optional[str] = None
) -> Dict[str, Any]:
    """
    Map IAM risks to NIST SP 800-53 controls.
    
    Args:
        role_name: Optional specific role to analyze
        cloud: Optional cloud filter
        
    Returns:
        Dictionary with NIST 800-53 compliance mapping
    """
    logger.info(f"Mapping IAM risks to NIST SP 800-53 for role: {role_name or 'all'}")
    
    # Detect escalation risks
    escalation_risks = detect_privilege_escalation(cloud=cloud)
    wildcard_risks = detect_wildcard_permissions(cloud=cloud)
    
    if role_name:
        escalation_risks = [r for r in escalation_risks if r["role"] == role_name]
        wildcard_risks = [r for r in wildcard_risks if r["role"] == role_name]
    
    # Map to NIST 800-53 controls
    compliance_gaps = []
    
    # AC-6: Least Privilege (CRITICAL)
    if escalation_risks or wildcard_risks:
        compliance_gaps.append({
            "control": "AC-6",
            "control_name": NIST80053_CONTROLS["AC-6"]["name"],
            "status": "NON-COMPLIANT",
            "severity": "HIGH",
            "finding": f"Least privilege violated: {len(escalation_risks)} roles have escalation permissions, {len(wildcard_risks)} roles have wildcards",
            "affected_roles": list(set([r["role"] for r in escalation_risks] + [r["role"] for r in wildcard_risks])),
            "recommendation": "Implement least-privilege: remove escalation permissions and replace wildcards with specific permissions"
        })
    
    # AC-6(1): Authorize Access to Security Functions
    security_function_roles = [
        r for r in escalation_risks
        if any("iam:" in p or "admin" in r["role"].lower() for p in r.get("risky_permissions", []))
    ]
    if security_function_roles:
        compliance_gaps.append({
            "control": "AC-6(1)",
            "control_name": NIST80053_CONTROLS["AC-6(1)"]["name"],
            "status": "NON-COMPLIANT",
            "severity": "HIGH",
            "finding": f"{len(security_function_roles)} roles have unrestricted access to security functions",
            "affected_roles": [r["role"] for r in security_function_roles],
            "recommendation": "Restrict security function access to authorized personnel only"
        })
    
    # AC-3: Access Enforcement
    if wildcard_risks:
        compliance_gaps.append({
            "control": "AC-3",
            "control_name": NIST80053_CONTROLS["AC-3"]["name"],
            "status": "NON-COMPLIANT",
            "severity": "MEDIUM",
            "finding": f"{len(wildcard_risks)} roles have wildcard permissions, violating access enforcement",
            "affected_roles": [r["role"] for r in wildcard_risks],
            "recommendation": "Replace wildcards with specific resource permissions"
        })
    
    # AC-2: Account Management
    # This would require additional data about role lifecycle
    # For now, we note that roles with high risk scores may indicate poor account management
    from ..ml.predict import batch_calculate_risk_scores
    risk_scores = batch_calculate_risk_scores(cloud=cloud)
    high_risk_roles = [r for r in risk_scores if r.get("risk_score", 0) > 70]
    
    if high_risk_roles:
        compliance_gaps.append({
            "control": "AC-2",
            "control_name": NIST80053_CONTROLS["AC-2"]["name"],
            "status": "REVIEW REQUIRED",
            "severity": "MEDIUM",
            "finding": f"{len(high_risk_roles)} roles have high risk scores, indicating potential account management issues",
            "affected_roles": [r["role"] for r in high_risk_roles[:10]],  # Limit for readability
            "recommendation": "Review and remediate high-risk roles following account management procedures"
        })
    
    # Calculate overall compliance score
    total_controls = len(NIST80053_CONTROLS)
    non_compliant = len([g for g in compliance_gaps if g["status"] == "NON-COMPLIANT"])
    compliance_score = ((total_controls - non_compliant) / total_controls * 100) if total_controls > 0 else 0
    
    return {
        "standard": "NIST SP 800-53",
        "scope": "IAM Access Control",
        "compliance_score": round(compliance_score, 2),
        "total_controls_assessed": total_controls,
        "non_compliant_controls": non_compliant,
        "compliance_gaps": compliance_gaps,
        "controls": NIST80053_CONTROLS,
        "assessment_date": None  # Would be set to current date in production
    }


def generate_nist80053_report(cloud: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive NIST SP 800-53 compliance report.
    
    Args:
        cloud: Optional cloud filter
        
    Returns:
        Complete compliance report
    """
    mapping = map_iam_risks_to_nist80053(cloud=cloud)
    
    # Add risk scores
    from ..ml.predict import batch_calculate_risk_scores
    risk_scores = batch_calculate_risk_scores(cloud=cloud)
    
    mapping["risk_summary"] = {
        "high": len([r for r in risk_scores if r.get("risk_level") == "high"]),
        "medium": len([r for r in risk_scores if r.get("risk_level") == "medium"]),
        "low": len([r for r in risk_scores if r.get("risk_level") == "low"])
    }
    
    mapping["high_risk_roles"] = len([r for r in risk_scores if r.get("risk_score", 0) > 70])
    
    return mapping


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== NIST SP 800-53 COMPLIANCE MAPPING ===")
    report = generate_nist80053_report()
    
    print(f"\nCompliance Score: {report['compliance_score']}%")
    print(f"Non-Compliant Controls: {report['non_compliant_controls']}")
    print("\nCompliance Gaps:")
    for gap in report["compliance_gaps"]:
        print(f"  - {gap['control']}: {gap['control_name']} ({gap['severity']})")
        print(f"    Finding: {gap['finding']}")
