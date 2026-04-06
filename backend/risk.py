"""Risk scoring API."""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException

from auth import CurrentUser
from graph_store import get_driver
from ingestion import get_permission_heatmap
from ml_engine import get_model_info, score_role
from models import ComplianceViolation, EscalationPath, RiskScore, WhatIfFeatures

router = APIRouter(prefix="/risk", tags=["risk"])


def _level_from_string(level: str) -> str:
    u = level.upper()
    if u in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        return u
    return "MEDIUM"


def _fetch_roles_from_neo4j() -> list[dict[str, Any]]:
    driver = get_driver()
    rows: list[dict[str, Any]] = []
    with driver.session() as session:
        result = session.run(
            """
            MATCH (r:IAMRole)
            RETURN r.id AS id, r.name AS name, r.cloud AS cloud,
                   r.permissions_count AS permissions_count,
                   r.has_admin_policy AS has_admin_policy,
                   r.has_star_action AS has_star_action,
                   r.trust_account_count AS trust_account_count,
                   r.cross_account AS cross_account,
                   r.age_days AS age_days,
                   r.inline_policy_count AS inline_policy_count,
                   r.managed_policy_count AS managed_policy_count
            """
        )
        for rec in result:
            rows.append(
                {
                    "id": rec["id"],
                    "name": rec["name"] or rec["id"],
                    "cloud": rec["cloud"] or "aws",
                    "permissions_count": int(rec["permissions_count"] or 0),
                    "has_admin_policy": int(rec["has_admin_policy"] or 0),
                    "has_star_action": int(rec["has_star_action"] or 0),
                    "trust_account_count": int(rec["trust_account_count"] or 0),
                    "cross_account": int(rec["cross_account"] or 0),
                    "age_days": int(rec["age_days"] or 0),
                    "inline_policy_count": int(rec["inline_policy_count"] or 0),
                    "managed_policy_count": int(rec["managed_policy_count"] or 0),
                }
            )
    return rows


def _load_escalation_paths() -> list[EscalationPath]:
    driver = get_driver()
    path_rows: list[EscalationPath] = []
    with driver.session() as session:
        result = session.run(
            """
            MATCH p = (r1:IAMRole)-[:CAN_ASSUME*1..3]->(r2:IAMRole)
            WHERE r1.id <> r2.id
            WITH p, nodes(p) AS ns
            RETURN [x IN ns | coalesce(x.name, x.id)] AS names,
                   ns[0].id AS r1id,
                   ns[size(ns)-1].id AS r2id
            LIMIT 500
            """
        )
        for rec in result:
            path_rows.append(
                EscalationPath(
                    from_role=rec["r1id"],
                    to_role=rec["r2id"],
                    path=list(rec["names"]),
                    risk_level="HIGH",
                )
            )
    return path_rows


def _count_escalations_for_role(paths: list[EscalationPath], role_id: str) -> int:
    n = 0
    for p in paths:
        if role_id in p.path or p.from_role == role_id or p.to_role == role_id:
            n += 1
    return n


@router.get("/scores", response_model=list[RiskScore])
async def list_risk_scores(_: CurrentUser):
    path_rows = _load_escalation_paths()
    roles = _fetch_roles_from_neo4j()
    out: list[RiskScore] = []
    for r in roles:
        feats = {
            "permissions_count": r["permissions_count"],
            "has_admin_policy": r["has_admin_policy"],
            "has_star_action": r["has_star_action"],
            "trust_account_count": r["trust_account_count"],
            "cross_account": r["cross_account"],
            "age_days": r["age_days"],
            "inline_policy_count": r["inline_policy_count"],
            "managed_policy_count": r["managed_policy_count"],
        }
        s = score_role(feats)
        esc = _count_escalations_for_role(path_rows, r["id"])
        out.append(
            RiskScore(
                identity_id=r["id"],
                name=r["name"],
                cloud=r["cloud"],
                risk_score=int(s["risk_score"]),
                level=_level_from_string(str(s["level"])),
                if_score=float(s["if_score"]),
                anomaly=bool(s["anomaly"]),
                permissions_count=int(r["permissions_count"]),
                escalation_paths=esc,
            )
        )
    out.sort(key=lambda x: x.risk_score, reverse=True)
    return out


@router.get("/score/{identity_id:path}", response_model=RiskScore)
async def get_one_score(identity_id: str, _: CurrentUser):
    decoded = unquote(identity_id)
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (r:IAMRole {id: $id})
            RETURN r.id AS id, r.name AS name, r.cloud AS cloud,
                   r.permissions_count AS permissions_count,
                   r.has_admin_policy AS has_admin_policy,
                   r.has_star_action AS has_star_action,
                   r.trust_account_count AS trust_account_count,
                   r.cross_account AS cross_account,
                   r.age_days AS age_days,
                   r.inline_policy_count AS inline_policy_count,
                   r.managed_policy_count AS managed_policy_count
            """,
            id=decoded,
        )
        rec = result.single()
        if not rec:
            raise HTTPException(status_code=404, detail="Role not found")

    r = {
        "id": rec["id"],
        "name": rec["name"] or rec["id"],
        "cloud": rec["cloud"] or "aws",
        "permissions_count": int(rec["permissions_count"] or 0),
        "has_admin_policy": int(rec["has_admin_policy"] or 0),
        "has_star_action": int(rec["has_star_action"] or 0),
        "trust_account_count": int(rec["trust_account_count"] or 0),
        "cross_account": int(rec["cross_account"] or 0),
        "age_days": int(rec["age_days"] or 0),
        "inline_policy_count": int(rec["inline_policy_count"] or 0),
        "managed_policy_count": int(rec["managed_policy_count"] or 0),
    }
    feats = {
        "permissions_count": r["permissions_count"],
        "has_admin_policy": r["has_admin_policy"],
        "has_star_action": r["has_star_action"],
        "trust_account_count": r["trust_account_count"],
        "cross_account": r["cross_account"],
        "age_days": r["age_days"],
        "inline_policy_count": r["inline_policy_count"],
        "managed_policy_count": r["managed_policy_count"],
    }
    s = score_role(feats)
    path_rows = _load_escalation_paths()
    esc = _count_escalations_for_role(path_rows, r["id"])
    return RiskScore(
        identity_id=r["id"],
        name=r["name"],
        cloud=r["cloud"],
        risk_score=int(s["risk_score"]),
        level=_level_from_string(str(s["level"])),
        if_score=float(s["if_score"]),
        anomaly=bool(s["anomaly"]),
        permissions_count=int(r["permissions_count"]),
        escalation_paths=esc,
    )


@router.post("/preview", response_model=RiskScore)
async def preview_whatif(body: WhatIfFeatures, _: CurrentUser):
    feats = body.model_dump()
    s = score_role(feats)
    return RiskScore(
        identity_id="synthetic:what-if",
        name="What-If Preview",
        cloud="aws",
        risk_score=int(s["risk_score"]),
        level=_level_from_string(str(s["level"])),
        if_score=float(s["if_score"]),
        anomaly=bool(s["anomaly"]),
        permissions_count=int(feats["permissions_count"]),
        escalation_paths=0,
    )


@router.get("/models", response_model=dict)
async def models_metadata(_: CurrentUser):
    return get_model_info()


@router.get("/heatmap", response_model=dict[str, int])
async def permission_heatmap(_: CurrentUser):
    return get_permission_heatmap()


compliance_router = APIRouter(prefix="/compliance", tags=["compliance"])


@compliance_router.get("/cis", response_model=list[ComplianceViolation])
async def cis_violations(_: CurrentUser):
    """CIS-style AWS IAM checks on ingested roles."""
    rows = _fetch_roles_from_neo4j()
    violations: list[ComplianceViolation] = []
    for r in rows:
        if int(r.get("has_star_action", 0)) == 1 or int(r.get("has_admin_policy", 0)) == 1:
            violations.append(
                ComplianceViolation(
                    role_arn=r["id"],
                    role_name=r["name"],
                    cloud=r["cloud"],
                    rule_id="CIS-1.16",
                    rule_name="No full administrative privileges via wildcards",
                    severity="HIGH",
                    detail="AdministratorAccess attached or Action wildcard detected in policies.",
                )
            )
        if int(r.get("age_days", 0)) > 90 and int(r.get("permissions_count", 0)) <= 1:
            violations.append(
                ComplianceViolation(
                    role_arn=r["id"],
                    role_name=r["name"],
                    cloud=r["cloud"],
                    rule_id="CIS-1.22",
                    rule_name="Unused or stale roles",
                    severity="MEDIUM",
                    detail="Role age exceeds 90 days with minimal effective permissions (proxy for unused).",
                )
            )
        if int(r.get("cross_account", 0)) == 1:
            violations.append(
                ComplianceViolation(
                    role_arn=r["id"],
                    role_name=r["name"],
                    cloud=r["cloud"],
                    rule_id="CIS-1.20",
                    rule_name="Cross-account trust without MFA enforcement (review)",
                    severity="HIGH",
                    detail="Cross-account principal in trust policy; verify MFA conditions on assume role.",
                )
            )
    return violations
