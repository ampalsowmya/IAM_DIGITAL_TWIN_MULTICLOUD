import logging
import time
from typing import Any, Dict, List

import httpx
from azure.identity import DefaultAzureCredential

from ..config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def _graph_get_all(path: str, token: str) -> List[Dict[str, Any]]:
    url = f"{GRAPH_BASE}/{path}"
    headers = {"Authorization": f"Bearer {token}"}
    out: List[Dict[str, Any]] = []
    delay = 1.0
    while url:
        for _ in range(5):
            try:
                resp = httpx.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                out.extend(data.get("value", []))
                url = data.get("@odata.nextLink")
                delay = 1.0
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("Graph request retry: %s", exc)
                time.sleep(delay)
                delay = min(delay * 2, 16.0)
        else:
            break
    return out


def ingest_azure_iam() -> List[Dict[str, Any]]:
    """Fetch Azure users/groups/service principals and role assignments."""
    if not (settings.AZURE_TENANT_ID and settings.AZURE_CLIENT_ID and settings.AZURE_CLIENT_SECRET):
        logger.warning("Azure credentials missing; returning empty dataset.")
        return []

    credential = DefaultAzureCredential()
    token = credential.get_token(GRAPH_SCOPE).token
    users = _graph_get_all("users?$select=id,displayName,mail,userPrincipalName", token)
    groups = _graph_get_all("groups?$select=id,displayName,mail", token)
    sps = _graph_get_all("servicePrincipals?$select=id,displayName,appId", token)
    role_assignments = _graph_get_all("roleManagement/directory/roleAssignments", token)

    entities: List[Dict[str, Any]] = []
    for u in users:
        entities.append(
            {
                "id": u["id"],
                "name": u.get("displayName") or u.get("userPrincipalName") or u["id"],
                "cloud": "azure",
                "type": "user",
                "permissions": [],
                "tags": [],
                "email": u.get("mail") or u.get("userPrincipalName"),
            }
        )
    for g in groups:
        entities.append(
            {
                "id": g["id"],
                "name": g.get("displayName", g["id"]),
                "cloud": "azure",
                "type": "group",
                "permissions": [],
                "tags": [],
                "email": g.get("mail"),
            }
        )
    for sp in sps:
        assigned = [a for a in role_assignments if a.get("principalId") == sp.get("id")]
        perms = [
            {
                "action": "azure:role_assignment",
                "resource": a.get("directoryScopeId", "/"),
                "effect": "Allow",
                "condition": {"roleDefinitionId": a.get("roleDefinitionId")},
            }
            for a in assigned
        ]
        entities.append(
            {
                "id": sp["id"],
                "name": sp.get("displayName", sp["id"]),
                "cloud": "azure",
                "type": "role",
                "permissions": perms,
                "tags": [{"key": "appId", "value": sp.get("appId")}],
                "email": None,
            }
        )
    return entities
