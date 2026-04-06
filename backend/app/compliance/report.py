from typing import Any, Dict, List

from .frameworks import FRAMEWORKS


def generate_compliance_report(framework: str, risk_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    controls = FRAMEWORKS.get(framework, [])
    high = [r for r in risk_scores if r.get("risk_score", 0) > 70]
    out = []
    for c in controls:
        status = "PASS"
        if high:
            status = "FAIL" if len(high) > 3 else "PARTIAL"
        out.append(
            {
                "id": c["id"],
                "name": c["name"],
                "status": status,
                "affected_identities": [h["identity_name"] for h in high][:10],
                "remediation_hint": "Reduce wildcard/admin permissions and enforce least privilege.",
            }
        )
    return {"framework": framework, "controls": out}

