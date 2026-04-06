# Example Outputs and Usage Scenarios

## Example 1: Escalation Detection

### Input
```python
from backend.app.graph.escalation import detect_all_escalation_risks

results = detect_all_escalation_risks(cloud="aws")
```

### Output
```json
{
  "direct_escalation": [
    {
      "role": "LambdaExecutionRole",
      "cloud": "aws",
      "risky_permissions": ["iam:PassRole", "sts:AssumeRole"],
      "risk_level": "high"
    },
    {
      "role": "EC2InstanceRole",
      "cloud": "aws",
      "risky_permissions": ["iam:AttachRolePolicy"],
      "risk_level": "high"
    }
  ],
  "wildcard_permissions": [
    {
      "role": "AdminRole",
      "cloud": "aws",
      "wildcard_permissions": ["iam:*", "s3:*"],
      "risk_level": "critical"
    }
  ]
}
```

## Example 2: What-If Simulation

### Input
```python
from backend.app.simulation.what_if import WhatIfSimulator

with WhatIfSimulator() as simulator:
    result = simulator.simulate_permission_removal(
        role_name="LambdaExecutionRole",
        permissions_to_remove=["iam:PassRole"],
        cloud="aws"
    )
```

### Output
```json
{
  "role": "LambdaExecutionRole",
  "permissions_removed": ["iam:PassRole"],
  "before": {
    "escalation_risks": [
      {
        "role": "LambdaExecutionRole",
        "risky_permissions": ["iam:PassRole", "sts:AssumeRole"]
      }
    ],
    "risk_count": 1
  },
  "after": {
    "escalation_risks": [
      {
        "role": "LambdaExecutionRole",
        "remaining_risky_permissions": ["sts:AssumeRole"]
      }
    ],
    "risk_count": 1
  },
  "risk_reduction": 0,
  "recommendation": "REVIEW REQUIRED"
}
```

## Example 3: ML Risk Scoring

### Input
```python
from backend.app.ml.predict import calculate_risk_score

score = calculate_risk_score("LambdaExecutionRole", cloud="aws")
```

### Output
```json
{
  "role": "LambdaExecutionRole",
  "cloud": "aws",
  "risk_score": 85,
  "risk_level": "high",
  "risk_probability": 0.85,
  "explainable_factors": {
    "top_contributing_factors": {
      "dangerous_perm_count": {
        "importance": 0.4,
        "value": 2,
        "contribution": 0.8
      },
      "wildcard_perm_count": {
        "importance": 0.3,
        "value": 1,
        "contribution": 0.3
      },
      "policy_count": {
        "importance": 0.15,
        "value": 5,
        "contribution": 0.75
      }
    },
    "primary_risk_indicators": [
      "dangerous_perm_count",
      "wildcard_perm_count",
      "policy_count"
    ]
  },
  "model_type": "random_forest"
}
```

## Example 4: LLM Governance Explanation

### Input
```python
from backend.app.llm.governance import explain_risk

explanation = explain_risk(
    role_name="LambdaExecutionRole",
    risk_score=85,
    risk_level="high",
    escalation_findings=[{
        "role": "LambdaExecutionRole",
        "risky_permissions": ["iam:PassRole", "sts:AssumeRole"]
    }],
    explainable_factors={
        "top_contributing_factors": {
            "dangerous_perm_count": {"importance": 0.4, "value": 2}
        }
    }
)
```

### Output
```json
{
  "role": "LambdaExecutionRole",
  "risk_score": 85,
  "risk_level": "high",
  "llm_explanation": "The LambdaExecutionRole has a high risk score of 85 due to several critical factors. First, the role possesses dangerous permissions including 'iam:PassRole' and 'sts:AssumeRole', which are commonly exploited for privilege escalation attacks. The 'iam:PassRole' permission allows the role to pass IAM roles to AWS services, potentially granting excessive permissions. The 'sts:AssumeRole' permission enables the role to assume other roles, creating a potential escalation path. To reduce risk, implement least-privilege by removing unnecessary permissions and restricting 'iam:PassRole' to specific, required roles only.",
  "llm_available": true,
  "escalation_findings": [...]
}
```

## Example 5: Compliance Mapping

### Input
```python
from backend.app.compliance import generate_iso27001_report

report = generate_iso27001_report(cloud="aws")
```

### Output
```json
{
  "standard": "ISO 27001",
  "scope": "IAM Access Control",
  "compliance_score": 70.0,
  "total_controls_assessed": 10,
  "non_compliant_controls": 3,
  "compliance_gaps": [
    {
      "control": "A.9.2.3",
      "control_name": "Management of privileged access rights",
      "status": "NON-COMPLIANT",
      "finding": "5 roles have privilege escalation permissions",
      "affected_roles": ["LambdaExecutionRole", "EC2InstanceRole", ...],
      "recommendation": "Remove or restrict escalation permissions following least-privilege"
    },
    {
      "control": "A.9.4.1",
      "control_name": "Information access restriction",
      "status": "NON-COMPLIANT",
      "finding": "2 roles have wildcard permissions",
      "affected_roles": ["AdminRole", ...],
      "recommendation": "Replace wildcard permissions with specific resource permissions"
    }
  ],
  "high_risk_roles": 3,
  "risk_summary": {
    "high": 3,
    "medium": 5,
    "low": 12
  }
}
```

## Example 6: Full Workflow

### Input
```bash
python -m backend.app.main --cloud aws
```

### Output (Summary)
```
================================================================
MULTI-CLOUD IAM DIGITAL TWIN - FULL WORKFLOW
================================================================

[1/6] IAM Data Ingestion
------------------------------------------------------------
Ingesting AWS IAM data...
[+] Processing role: LambdaExecutionRole
[+] Processing role: EC2InstanceRole
...
✅ AWS IAM ingestion complete: {'status': 'success', 'roles_processed': 25, 'policies_processed': 45}

[2/6] Privilege Escalation Detection
------------------------------------------------------------
Detected 5 roles with escalation risks

[3/6] ML Risk Scoring
------------------------------------------------------------
Training/loading ML models...
RandomForest trained: R²=0.85, MSE=0.0234
XGBoost trained: R²=0.87, MSE=0.0210
Calculating risk scores...
Calculated risk scores for 25 roles
High risk: 3, Medium: 5, Low: 17

[4/6] LLM Governance Explanations
------------------------------------------------------------
Generating LLM explanation for LambdaExecutionRole...
Generated 5 LLM explanations

[5/6] Compliance Mapping
------------------------------------------------------------
Generating ISO 27001 compliance report...
Generating NIST SP 800-53 compliance report...
ISO 27001 Compliance: 70.0%
NIST 800-53 Compliance: 65.0%

[6/6] Generating Summary
------------------------------------------------------------
================================================================
WORKFLOW COMPLETE
================================================================
Summary: {
  'total_roles_analyzed': 25,
  'escalation_risks': 5,
  'wildcard_risks': 2,
  'high_risk_roles': 3,
  'iso27001_compliance': 70.0,
  'nist80053_compliance': 65.0
}
```

## Example 7: Remediation Script Generation

### Input
```python
from backend.app.simulation.remediation import generate_remediation_report

report = generate_remediation_report("LambdaExecutionRole", "aws")
```

### Output
```json
{
  "role": "LambdaExecutionRole",
  "cloud": "aws",
  "current_risk_score": 85,
  "estimated_risk_after_remediation": 25.5,
  "risk_reduction_percentage": 70.0,
  "remediation_suggestions": {
    "current_risks": ["iam:PassRole", "sts:AssumeRole"],
    "suggestions": [
      {
        "permission": "iam:PassRole",
        "action": "REMOVE",
        "reason": "Escalation risk: iam:PassRole allows privilege escalation",
        "alternative": "Use iam:PassRole with resource constraints"
      }
    ]
  },
  "dry_run_script": "#!/bin/bash\n# DRY-RUN REMEDIATION SCRIPT FOR AWS IAM\n# Role: LambdaExecutionRole\n# ...",
  "next_steps": [
    "1. Review remediation suggestions",
    "2. Test in non-production environment",
    "3. Execute dry-run script to verify changes",
    "4. Get approval from security team",
    "5. Execute remediation during maintenance window",
    "6. Monitor for any service disruptions"
  ]
}
```

## Example 8: Cypher Queries Used

### Escalation Detection Query
```cypher
MATCH (r:Role {cloud: 'aws'})-[:HAS_POLICY]->(:Policy)-[:ALLOWS]->(p:Permission)
WHERE p.name IN ['iam:PassRole', 'iam:AttachRolePolicy', 'sts:AssumeRole']
RETURN r.name AS role, r.cloud AS cloud, collect(DISTINCT p.name) AS risky_permissions
```

### Wildcard Permission Detection
```cypher
MATCH (r:Role)-[:HAS_POLICY]->(:Policy)-[:ALLOWS]->(p:Permission)
WHERE p.name CONTAINS '*'
RETURN r.name AS role, r.cloud AS cloud, collect(DISTINCT p.name) AS wildcard_permissions
```

### Feature Extraction Query
```cypher
MATCH (r:Role {cloud: 'aws'})
OPTIONAL MATCH (r)-[:HAS_POLICY]->(p:Policy)
OPTIONAL MATCH (p)-[:ALLOWS]->(perm:Permission)
WITH r, p, perm
RETURN
    r.name AS role,
    r.cloud AS cloud,
    count(DISTINCT p) AS policy_count,
    collect(DISTINCT perm.name) AS permissions
```

## Notes

- All examples use real data structures from the implementation
- LLM explanations are examples - actual output depends on LLM provider and model
- Compliance scores are calculated based on detected risks
- Risk scores are on 0-100 scale (0=low risk, 100=critical risk)
