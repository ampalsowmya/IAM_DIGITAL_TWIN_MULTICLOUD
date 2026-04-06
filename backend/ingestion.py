"""AWS IAM ingestion and scheduled sync."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends

from auth import CurrentUser
from config import get_settings
from graph_store import clear_cloud_nodes, get_driver, init_schema, store_ingestion_batch
from models import IngestProgress, IngestResponse

ingest_state: dict[str, Any] = {
    "status": "idle",
    "percent": 0.0,
    "roles_processed": 0,
    "total_roles": 0,
    "last_scan_utc": "",
    "last_error": "",
    "heatmap": {
        "iam:PassRole": 0,
        "iam:AttachRole": 0,
        "sts:AssumeRole": 0,
        "iam:*": 0,
        "s3:*": 0,
        "RoleAssign.Write": 0,
    },
}

activity_log: list[dict[str, Any]] = []


def log_activity(level: str, title: str, detail: str) -> None:
    activity_log.insert(
        0,
        {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "level": level,
            "title": title,
            "detail": detail,
        },
    )
    del activity_log[100:]

router = APIRouter(prefix="/ingest", tags=["ingestion"])


def _normalize_statement(stmt: Any) -> list[dict[str, Any]]:
    if isinstance(stmt, list):
        return [s for s in stmt if isinstance(s, dict)]
    if isinstance(stmt, dict):
        return [stmt]
    return []


def _extract_actions_from_policy_doc(doc: dict[str, Any]) -> tuple[int, bool]:
    """Count Action entries; detect wildcard admin."""
    count = 0
    has_star = False
    stmts = _normalize_statement(doc.get("Statement", []))
    for st in stmts:
        eff = st.get("Effect", "Allow")
        if eff != "Allow":
            continue
        act = st.get("Action")
        if act is None:
            not_act = st.get("NotAction")
            if isinstance(not_act, str):
                count += 1
            elif isinstance(not_act, list):
                count += len(not_act)
            continue
        if isinstance(act, str):
            actions = [act]
        else:
            actions = list(act)
        for a in actions:
            count += 1
            if a == "*" or a == "iam:*" or a == "s3:*":
                has_star = True
        if "*" in actions:
            has_star = True
    return count, has_star


def _parse_trust_accounts(
    assume_doc: dict[str, Any], my_account: str
) -> tuple[int, bool, list[str]]:
    """Trust account count, cross-account flag, principal role ARNs for graph edges."""
    trust_accounts: set[str] = set()
    cross = False
    principal_roles: list[str] = []
    stmts = _normalize_statement(assume_doc.get("Statement", []))
    for st in stmts:
        if st.get("Effect") != "Allow":
            continue
        pr = st.get("Principal")
        if not isinstance(pr, dict):
            continue
        for key in ("AWS", "Federated"):
            val = pr.get(key)
            if val is None:
                continue
            if isinstance(val, str):
                vals = [val]
            else:
                vals = list(val)
            for v in vals:
                m = re.search(r"arn:aws:iam::(\d{12}):", v)
                if m:
                    trust_accounts.add(m.group(1))
                if ":role/" in v and v.startswith("arn:aws:iam::"):
                    principal_roles.append(v)
    for acct in trust_accounts:
        if my_account and acct != my_account:
            cross = True
            break
    return len(trust_accounts), cross, principal_roles


def _policy_json_to_counts(policy_doc: dict[str, Any]) -> tuple[int, bool]:
    return _extract_actions_from_policy_doc(policy_doc)


def _feed_heatmap_from_action(action: str, heatmap: dict[str, int]) -> None:
    a = action.strip()
    al = a.lower()
    if al in ("*", "iam:*"):
        heatmap["iam:*"] += 1
    elif al == "s3:*" or (al.startswith("s3:") and "*" in al):
        heatmap["s3:*"] += 1
    elif "passrole" in al and "iam" in al:
        heatmap["iam:PassRole"] += 1
    elif "attachrole" in al and "iam" in al:
        heatmap["iam:AttachRole"] += 1
    elif "assumerole" in al and ("sts" in al or al.startswith("sts:")):
        heatmap["sts:AssumeRole"] += 1
    elif "roleassign" in al or "roleassign.write" in al:
        heatmap["RoleAssign.Write"] += 1


def _collect_heatmap_from_policy_doc(doc: dict[str, Any], heatmap: dict[str, int]) -> None:
    stmts = _normalize_statement(doc.get("Statement", []))
    for st in stmts:
        if st.get("Effect") != "Allow":
            continue
        act = st.get("Action")
        if act is None:
            continue
        actions = [act] if isinstance(act, str) else list(act)
        for a in actions:
            _feed_heatmap_from_action(str(a), heatmap)


def ingest_aws_iam() -> IngestResponse:
    """Full AWS IAM role ingestion into Neo4j."""
    global ingest_state
    settings = get_settings()
    ingest_state["status"] = "running"
    ingest_state["last_error"] = ""
    ingest_state["percent"] = 0.0
    ingest_state["roles_processed"] = 0
    heatmap: dict[str, int] = {
        "iam:PassRole": 0,
        "iam:AttachRole": 0,
        "sts:AssumeRole": 0,
        "iam:*": 0,
        "s3:*": 0,
        "RoleAssign.Write": 0,
    }
    log_activity("info", "Workflow started", "IAM ingestion job initialized")

    try:
        session_kw: dict[str, Any] = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kw["aws_access_key_id"] = settings.aws_access_key_id
            session_kw["aws_secret_access_key"] = settings.aws_secret_access_key
        sess = boto3.session.Session(**session_kw)
        iam = sess.client("iam")
        sts = sess.client("sts")
        identity = sts.get_caller_identity()
        my_acct = identity.get("Account", "")

        paginator = iam.get_paginator("list_roles")
        role_summaries: list[dict[str, Any]] = []
        for page in paginator.paginate():
            role_summaries.extend(page.get("Roles", []))

        total = len(role_summaries)
        ingest_state["total_roles"] = total
        if total == 0:
            ingest_state["status"] = "completed"
            ingest_state["percent"] = 100.0
            ingest_state["heatmap"] = heatmap
            ingest_state["last_scan_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            log_activity("info", "Ingestion completed", "No IAM roles returned by AWS")
            return IngestResponse(
                status="completed",
                roles_ingested=0,
                relationships_created=0,
                cloud="aws",
            )

        roles_out: list[dict[str, Any]] = []
        policies_out: list[dict[str, Any]] = []
        relationships: list[dict[str, str]] = []
        policy_ids_seen: set[str] = set()
        rel_count_estimate = 0

        for idx, role in enumerate(role_summaries):
            role_name = role["RoleName"]
            role_arn = role["Arn"]
            create_date = role.get("CreateDate")
            if hasattr(create_date, "isoformat"):
                create_iso = create_date.isoformat()
            else:
                create_iso = str(create_date)
            age_days = 0
            if create_date:
                try:
                    cd = create_date
                    if cd.tzinfo is None:
                        cd = cd.replace(tzinfo=timezone.utc)
                    age_days = max(0, (datetime.now(timezone.utc) - cd).days)
                except (TypeError, ValueError):
                    age_days = 0

            assume_doc = {}
            try:
                assume = iam.get_role(RoleName=role_name)["Role"]
                assume_doc = assume.get("AssumeRolePolicyDocument") or {}
            except (ClientError, BotoCoreError):
                assume_doc = {}

            trust_n, cross, principal_roles = _parse_trust_accounts(assume_doc, my_acct)

            attached = []
            try:
                ap = iam.list_attached_role_policies(RoleName=role_name)
                attached = ap.get("AttachedPolicies", [])
            except (ClientError, BotoCoreError):
                attached = []

            inline_names: list[str] = []
            try:
                inline_names = iam.list_role_policies(RoleName=role_name).get("PolicyNames", [])
            except (ClientError, BotoCoreError):
                inline_names = []

            perm_total = 0
            has_star = False
            has_admin = False

            for pol in attached:
                pol_arn = pol.get("PolicyArn", "")
                pol_name = pol.get("PolicyName", "")
                if "AdministratorAccess" in pol_name:
                    has_admin = True
                if pol_arn not in policy_ids_seen:
                    policy_ids_seen.add(pol_arn)
                    policies_out.append(
                        {
                            "id": pol_arn,
                            "name": pol_name,
                            "cloud": "aws",
                        }
                    )
                relationships.append(
                    {"from_id": role_arn, "to_id": pol_arn, "type": "HAS_POLICY"}
                )
                rel_count_estimate += 1
                try:
                    vers = iam.get_policy(PolicyArn=pol_arn)["Policy"]
                    dv = vers["DefaultVersionId"]
                    doc = iam.get_policy_version(PolicyArn=pol_arn, VersionId=dv)["PolicyVersion"]["Document"]
                    c, hs = _policy_json_to_counts(doc)
                    _collect_heatmap_from_policy_doc(doc, heatmap)
                    perm_total += c
                    has_star = has_star or hs
                except (ClientError, BotoCoreError, KeyError):
                    pass

            for iname in inline_names:
                pol_id = f"{role_arn}::inline::{iname}"
                if pol_id not in policy_ids_seen:
                    policy_ids_seen.add(pol_id)
                    policies_out.append(
                        {
                            "id": pol_id,
                            "name": iname,
                            "cloud": "aws",
                        }
                    )
                relationships.append(
                    {"from_id": role_arn, "to_id": pol_id, "type": "HAS_POLICY"}
                )
                rel_count_estimate += 1
                try:
                    inline_doc = iam.get_role_policy(RoleName=role_name, PolicyName=iname)["PolicyDocument"]
                    c, hs = _policy_json_to_counts(inline_doc)
                    _collect_heatmap_from_policy_doc(inline_doc, heatmap)
                    perm_total += c
                    has_star = has_star or hs
                except (ClientError, BotoCoreError, KeyError):
                    pass

            for pr_arn in principal_roles:
                if pr_arn.startswith("arn:aws:iam::") and ":role/" in pr_arn:
                    relationships.append(
                        {"from_id": pr_arn, "to_id": role_arn, "type": "CAN_ASSUME"}
                    )
                    rel_count_estimate += 1

            roles_out.append(
                {
                    "id": role_arn,
                    "name": role_name,
                    "cloud": "aws",
                    "create_date": create_iso,
                    "permissions_count": perm_total,
                    "has_admin_policy": 1 if has_admin else 0,
                    "has_star_action": 1 if has_star else 0,
                    "trust_account_count": trust_n,
                    "cross_account": 1 if cross else 0,
                    "age_days": age_days,
                    "inline_policy_count": len(inline_names),
                    "managed_policy_count": len(attached),
                    "assume_policy_json": json.dumps(assume_doc)[:20000],
                }
            )
            if has_star and perm_total > 0:
                log_activity(
                    "warn",
                    f"Role ingested: {role_name}",
                    f"{perm_total} permissions detected — review wildcards",
                )

            ingest_state["roles_processed"] = idx + 1
            ingest_state["percent"] = round(100.0 * (idx + 1) / total, 2)

        driver = get_driver()
        with driver.session() as neo_session:
            init_schema(neo_session)
            clear_cloud_nodes(neo_session, "aws")
            rel_created = store_ingestion_batch(
                neo_session,
                {
                    "roles": roles_out,
                    "policies": policies_out,
                    "relationships": relationships,
                },
            )

        ingest_state["status"] = "completed"
        ingest_state["percent"] = 100.0
        ingest_state["last_scan_utc"] = datetime.now(timezone.utc).strftime(
            "%b %d %Y %H:%M UTC"
        )
        ingest_state["heatmap"] = heatmap
        log_activity(
            "info",
            "Ingestion completed",
            f"{len(roles_out)} roles synced to Neo4j graph",
        )

        return IngestResponse(
            status="completed",
            roles_ingested=len(roles_out),
            relationships_created=rel_created,
            cloud="aws",
        )
    except (ClientError, BotoCoreError, ValueError, RuntimeError, OSError) as e:
        ingest_state["status"] = "error"
        ingest_state["last_error"] = str(e)
        log_activity("error", "Ingestion failed", str(e))
        return IngestResponse(
            status=f"error: {e}",
            roles_ingested=0,
            relationships_created=0,
            cloud="aws",
        )


@router.post("/{cloud}", response_model=IngestResponse)
async def trigger_ingest(cloud: str, _: CurrentUser):
    c = cloud.lower().strip()
    if c == "aws":
        return ingest_aws_iam()
    if c in ("azure", "gcp"):
        return IngestResponse(
            status="stub: not implemented for this cloud",
            roles_ingested=0,
            relationships_created=0,
            cloud=c,
        )
    return IngestResponse(
        status="unknown cloud",
        roles_ingested=0,
        relationships_created=0,
        cloud=cloud,
    )


@router.get("/progress", response_model=IngestProgress)
async def ingest_progress(_: CurrentUser):
    return IngestProgress(
        status=str(ingest_state.get("status", "idle")),
        percent=float(ingest_state.get("percent", 0.0)),
        roles_processed=int(ingest_state.get("roles_processed", 0)),
        total_roles=int(ingest_state.get("total_roles", 0)),
        last_scan_utc=str(ingest_state.get("last_scan_utc", "")),
    )


@router.get("/activity", response_model=list[dict[str, Any]])
async def recent_activity(_: CurrentUser):
    return list(activity_log[:50])


def get_last_scan_timestamp() -> str:
    return str(ingest_state.get("last_scan_utc", ""))


def get_permission_heatmap() -> dict[str, int]:
    h = ingest_state.get("heatmap")
    if isinstance(h, dict):
        return {str(k): int(v) for k, v in h.items()}
    return {
        "iam:PassRole": 0,
        "iam:AttachRole": 0,
        "sts:AssumeRole": 0,
        "iam:*": 0,
        "s3:*": 0,
        "RoleAssign.Write": 0,
    }
