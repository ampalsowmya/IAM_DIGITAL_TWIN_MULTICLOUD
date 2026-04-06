"""
Automated Remediation Module
============================
This module generates least-privilege remediation suggestions and scripts.

IMPORTANT: All remediation scripts are DRY-RUN ONLY by default.
Never execute remediation without explicit approval and testing.
"""
import logging
from typing import List, Dict, Any, Optional
from .what_if import WhatIfSimulator
from ..graph.escalation import detect_privilege_escalation, detect_wildcard_permissions
from ..ml.predict import calculate_risk_score

logger = logging.getLogger(__name__)


def generate_least_privilege_suggestions(role_name: str, cloud: str) -> Dict[str, Any]:
    """
    Generate least-privilege policy suggestions for a role.
    
    Analyzes current permissions and suggests minimal required permissions.
    
    Args:
        role_name: Role to analyze
        cloud: Cloud provider
        
    Returns:
        Dictionary with remediation suggestions
    """
    with WhatIfSimulator() as simulator:
        # Get current risky permissions
        escalation_risks = detect_privilege_escalation(cloud=cloud)
        role_risks = [r for r in escalation_risks if r["role"] == role_name]
        
        if not role_risks:
            return {
                "role": role_name,
                "status": "no_risks",
                "message": "No escalation risks detected for this role"
            }
        
        risky_permissions = role_risks[0]["risky_permissions"]
        
        # Generate suggestions
        suggestions = []
        for perm in risky_permissions:
            suggestions.append({
                "permission": perm,
                "action": "REMOVE" if perm in risky_permissions else "KEEP",
                "reason": f"Escalation risk: {perm} allows privilege escalation",
                "alternative": _suggest_alternative_permission(perm, cloud)
            })
        
        return {
            "role": role_name,
            "cloud": cloud,
            "current_risks": risky_permissions,
            "suggestions": suggestions,
            "recommended_actions": [
                {
                    "type": "remove_permissions",
                    "permissions": risky_permissions,
                    "dry_run_script": _generate_dry_run_script(role_name, risky_permissions, cloud)
                }
            ]
        }


def _suggest_alternative_permission(permission: str, cloud: str) -> Optional[str]:
    """
    Suggest a more restrictive alternative to a risky permission.
    
    Args:
        permission: Risky permission
        cloud: Cloud provider
        
    Returns:
        Alternative permission or None
    """
    # Example: Suggest resource-specific permissions instead of wildcards
    alternatives = {
        "iam:*": "Use specific iam:Get*, iam:List* permissions",
        "s3:*": "Use specific s3:GetObject, s3:PutObject for required buckets",
        "iam:PassRole": "Use iam:PassRole with resource constraints",
    }
    
    for risky, alt in alternatives.items():
        if risky in permission:
            return alt
    
    return None


def _generate_dry_run_script(role_name: str, permissions: List[str], cloud: str) -> str:
    """
    Generate a dry-run remediation script.
    
    Args:
        role_name: Role name
        permissions: Permissions to remove
        cloud: Cloud provider
        
    Returns:
        Script content as string
    """
    if cloud == "aws":
        script = f"""#!/bin/bash
# DRY-RUN REMEDIATION SCRIPT FOR AWS IAM
# Role: {role_name}
# Permissions to remove: {', '.join(permissions)}
# 
# WARNING: This is a DRY-RUN script. Review before executing.
# To execute, remove the --dry-run flag and uncomment the commands.

# Example: Remove inline policy with risky permissions
# aws iam delete-role-policy --role-name {role_name} --policy-name <policy-name> --dry-run

# Example: Detach managed policy
# aws iam detach-role-policy --role-name {role_name} --policy-arn <policy-arn> --dry-run

echo "DRY-RUN: Would remove permissions {permissions} from role {role_name}"
"""
    elif cloud == "azure":
        script = f"""# PowerShell DRY-RUN REMEDIATION SCRIPT FOR AZURE AD
# Role: {role_name}
# Permissions to remove: {', '.join(permissions)}
#
# WARNING: This is a DRY-RUN script. Review before executing.

# Example: Remove role assignment (dry-run simulation)
# Connect-AzAccount
# Get-AzRoleAssignment -RoleDefinitionName "{role_name}" | Format-List
# # Remove-AzRoleAssignment -ObjectId <object-id> -RoleDefinitionName "{role_name}" -WhatIf

Write-Host "DRY-RUN: Would remove permissions {permissions} from role {role_name}"
"""
    else:
        script = f"""# REMEDIATION SCRIPT FOR {cloud.upper()}
# Role: {role_name}
# Permissions to remove: {', '.join(permissions)}
# 
# WARNING: Review and customize for your cloud provider.
"""
    
    return script


def generate_remediation_report(role_name: str, cloud: str) -> Dict[str, Any]:
    """
    Generate comprehensive remediation report for a role.
    
    Args:
        role_name: Role to remediate
        cloud: Cloud provider
        
    Returns:
        Complete remediation report
    """
    suggestions = generate_least_privilege_suggestions(role_name, cloud)
    
    # Calculate risk score before and after
    from ..ml.predict import calculate_risk_score
    current_risk = calculate_risk_score(role_name, cloud)
    
    # Estimate risk after remediation
    estimated_risk = current_risk * 0.3  # Assume 70% risk reduction
    
    return {
        "role": role_name,
        "cloud": cloud,
        "current_risk_score": current_risk,
        "estimated_risk_after_remediation": estimated_risk,
        "risk_reduction_percentage": ((current_risk - estimated_risk) / current_risk * 100) if current_risk > 0 else 0,
        "remediation_suggestions": suggestions,
        "dry_run_script": _generate_dry_run_script(role_name, suggestions.get("current_risks", []), cloud),
        "next_steps": [
            "1. Review remediation suggestions",
            "2. Test in non-production environment",
            "3. Execute dry-run script to verify changes",
            "4. Get approval from security team",
            "5. Execute remediation during maintenance window",
            "6. Monitor for any service disruptions"
        ]
    }


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example remediation report
    report = generate_remediation_report("ExampleRole", "aws")
    print("\n=== REMEDIATION REPORT ===")
    print(f"Role: {report['role']}")
    print(f"Current Risk: {report['current_risk_score']:.2f}")
    print(f"Estimated Risk After: {report['estimated_risk_after_remediation']:.2f}")
    print(f"Risk Reduction: {report['risk_reduction_percentage']:.1f}%")
