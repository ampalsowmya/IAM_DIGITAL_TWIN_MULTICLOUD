import logging
import time
from typing import Any, Dict, List

import boto3

from ..config import settings

logger = logging.getLogger(__name__)


def _paginate_with_backoff(paginator, **kwargs):
    delay = 1.0
    for _ in range(5):
        try:
            return paginator.paginate(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AWS pagination throttled/retried: %s", exc)
            time.sleep(delay)
            delay = min(delay * 2, 16.0)
    return paginator.paginate(**kwargs)


def _get_iam_client():
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        return boto3.client(
            "iam",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return boto3.client("iam", region_name=settings.AWS_REGION)


def _extract_permissions_from_document(policy_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    permissions: List[Dict[str, Any]] = []
    statements = policy_doc.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    for stmt in statements:
        action = stmt.get("Action", [])
        resource = stmt.get("Resource", "*")
        effect = stmt.get("Effect", "Deny")
        condition = stmt.get("Condition", {})
        if isinstance(action, str):
            action = [action]
        if isinstance(resource, str):
            resource = [resource]
        for act in action:
            for res in resource:
                permissions.append(
                    {
                        "action": act,
                        "resource": res,
                        "effect": effect,
                        "condition": condition,
                    }
                )
    return permissions


def ingest_aws_iam() -> List[Dict[str, Any]]:
    """Fetch AWS IAM users/groups/roles and normalize into unified IAM schema."""
    client = _get_iam_client()
    entities: List[Dict[str, Any]] = []


    for page in _paginate_with_backoff(client.get_paginator("list_users")):
        for user in page.get("Users", []):
            entities.append(
                {
                    "id": user["UserId"],
                    "name": user["UserName"],
                    "cloud": "aws",
                    "type": "user",
                    "permissions": [],
                    "tags": user.get("Tags", []),
                    "email": next(
                        (
                            t["Value"]
                            for t in user.get("Tags", [])
                            if t.get("Key", "").lower() == "email"
                        ),
                        None,
                    ),
                }
            )


    for page in _paginate_with_backoff(client.get_paginator("list_groups")):
        for group in page.get("Groups", []):
            entities.append(
                {
                    "id": group["GroupId"],
                    "name": group["GroupName"],
                    "cloud": "aws",
                    "type": "group",
                    "permissions": [],
                    "tags": [],
                    "email": None,
                }
            )


    for page in _paginate_with_backoff(client.get_paginator("list_roles")):
        for role in page.get("Roles", []):
            permissions: List[Dict[str, Any]] = []
            role_name = role["RoleName"]


            for p in _paginate_with_backoff(
                client.get_paginator("list_attached_role_policies"),
                RoleName=role_name,
            ):
                for pol in p.get("AttachedPolicies", []):
                    pol_meta = client.get_policy(PolicyArn=pol["PolicyArn"])["Policy"]
                    ver = client.get_policy_version(
                        PolicyArn=pol["PolicyArn"],
                        VersionId=pol_meta["DefaultVersionId"],
                    )
                    permissions.extend(
                        _extract_permissions_from_document(
                            ver["PolicyVersion"]["Document"]
                        )
                    )

            for p in _paginate_with_backoff(
                client.get_paginator("list_role_policies"),
                RoleName=role_name,
            ):
                for policy_name in p.get("PolicyNames", []):
                    doc = client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                    permissions.extend(_extract_permissions_from_document(doc["PolicyDocument"]))

            entities.append(
                {
                    "id": role["RoleId"],
                    "name": role_name,
                    "cloud": "aws",
                    "type": "role",
                    "permissions": permissions,
                    "tags": role.get("Tags", []),
                    "email": next(
                        (
                            t["Value"]
                            for t in role.get("Tags", [])
                            if t.get("Key", "").lower() == "email"
                        ),
                        None,
                    ),
                }
            )


    # keep known working roles if present
    preferred = {
        "AdminRole",
        "AWSServiceRoleForResourceExplorer",
        "AWSServiceRoleForSupport",
        "AWSServiceRoleForTrustedAdvisor",
        "BreakGlassRole",
    }
    entities.sort(key=lambda e: (e["name"] not in preferred, e["name"]))
    return entities
