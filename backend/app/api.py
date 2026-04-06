"""
FastAPI Backend API Layer
=========================
RESTful API endpoints that wrap existing business logic.
No logic changes - only API exposure.
"""
import logging
import warnings
import sys
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Fix Unicode logging on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from .config import settings
from .graph.escalation import detect_all_escalation_risks
from .ml.predict import batch_calculate_risk_scores, calculate_risk_score
from .llm.governance import explain_risk
from .compliance import generate_iso27001_report, generate_nist80053_report
from .graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Cloud IAM Digital Twin API",
    description="API for IAM risk analysis, escalation detection, and compliance mapping",
    version="1.0.0"
)

# CORS middleware for frontend
frontend_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DEFAULT_CLOUD = (settings.default_cloud or "aws").lower()


def _effective_cloud(cloud: Optional[str]) -> str:
    """Return the effective cloud value, defaulting to AWS-only mode."""
    value = (cloud or DEFAULT_CLOUD or "aws").lower()
    return "aws" if value not in {"aws"} else value


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to ensure JSON errors are always returned
    instead of HTML stack traces.
    """
    logger.error(f"Unhandled exception for path {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
        },
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = Neo4jClient()
        client.driver.verify_connectivity()
        client.close()
        return {"status": "healthy", "neo4j": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "neo4j": "disconnected", "error": str(e)}


@app.get("/api/summary")
async def get_summary(cloud: Optional[str] = None):
    """Get overall system summary."""
    try:
        cloud = _effective_cloud(cloud)
        # Get risk scores
        risk_scores = batch_calculate_risk_scores(cloud=cloud)
        
        # Get escalation risks
        escalation_results = detect_all_escalation_risks(cloud=cloud)
        
        # Get compliance
        iso_report = generate_iso27001_report(cloud=cloud)
        nist_report = generate_nist80053_report(cloud=cloud)
        
        return {
            "total_roles": len(risk_scores),
            "risk_summary": {
                "high": len([r for r in risk_scores if r.get("risk_level") == "high"]),
                "medium": len([r for r in risk_scores if r.get("risk_level") == "medium"]),
                "low": len([r for r in risk_scores if r.get("risk_level") == "low"])
            },
            "escalation_risks": {
                "direct": len(escalation_results.get("direct_escalation", [])),
                "wildcard": len(escalation_results.get("wildcard_permissions", []))
            },
            "compliance": {
                "iso27001": iso_report.get("compliance_score", 0),
                "nist80053": nist_report.get("compliance_score", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error in summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roles")
async def get_roles(cloud: Optional[str] = None):
    """Get all roles with risk scores."""
    try:
        cloud = _effective_cloud(cloud)
        risk_scores = batch_calculate_risk_scores(cloud=cloud)
        return {"roles": risk_scores}
    except Exception as e:
        logger.error(f"Error fetching roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roles/{role_name}")
async def get_role_detail(role_name: str, cloud: Optional[str] = None):
    """Get detailed information for a specific role."""
    try:
        cloud = _effective_cloud(cloud)
        # Get risk score
        risk_score = calculate_risk_score(role_name, cloud=cloud)
        
        # Get escalation findings
        escalation_results = detect_all_escalation_risks(cloud=cloud)
        role_escalation = [r for r in escalation_results.get("direct_escalation", []) if r["role"] == role_name]
        role_wildcards = [r for r in escalation_results.get("wildcard_permissions", []) if r["role"] == role_name]
        
        # Get permissions
        client = Neo4jClient()
        permissions = client.get_role_permissions(role_name, cloud=cloud)
        client.close()
        
        # Get LLM explanation (graceful fallback)
        try:
            explanation = explain_risk(
                role_name=role_name,
                risk_score=risk_score.get("risk_score", 0),
                risk_level=risk_score.get("risk_level", "unknown"),
                escalation_findings=role_escalation,
                explainable_factors=risk_score.get("explainable_factors", {})
            )
            llm_explanation = explanation.get("llm_explanation", "LLM not configured")
            llm_available = explanation.get("llm_available", False)
        except Exception as e:
            logger.warning(f"LLM explanation failed: {e}")
            llm_explanation = f"Rule-based analysis: Role has risk score {risk_score.get('risk_score', 0)} due to {len(role_escalation)} escalation risks and {len(role_wildcards)} wildcard permissions."
            llm_available = False
        
        # Get compliance gaps
        iso_report = generate_iso27001_report(cloud=cloud)
        nist_report = generate_nist80053_report(cloud=cloud)
        
        compliance_gaps = []
        for gap in iso_report.get("compliance_gaps", []):
            if role_name in gap.get("affected_roles", []):
                compliance_gaps.append({
                    "standard": "ISO 27001",
                    "control": gap.get("control"),
                    "finding": gap.get("finding")
                })
        for gap in nist_report.get("compliance_gaps", []):
            if role_name in gap.get("affected_roles", []):
                compliance_gaps.append({
                    "standard": "NIST SP 800-53",
                    "control": gap.get("control"),
                    "finding": gap.get("finding")
                })
        
        return {
            "role": role_name,
            "cloud": risk_score.get("cloud", cloud),
            "risk_score": risk_score.get("risk_score", 0),
            "risk_level": risk_score.get("risk_level", "unknown"),
            "permissions": permissions,
            "escalation_risks": role_escalation,
            "wildcard_risks": role_wildcards,
            "compliance_gaps": compliance_gaps,
            "llm_explanation": llm_explanation,
            "llm_available": llm_available,
            "explainable_factors": risk_score.get("explainable_factors", {})
        }
    except Exception as e:
        logger.error(f"Error fetching role detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph")
async def get_graph(cloud: Optional[str] = None, limit: int = 100):
    """Get graph data for visualization."""
    try:
        cloud = _effective_cloud(cloud)
        client = Neo4jClient()

        query = """
        MATCH (r:Role {cloud: $cloud})-[:HAS_POLICY]->(p:Policy)-[:HAS_PERMISSION]->(perm:Permission)
        RETURN r.name AS role, r.cloud AS role_cloud, p.name AS policy, perm.name AS permission
        LIMIT $limit
        """
        
        with client.driver.session() as session:
            result = session.run(query, cloud=cloud, limit=limit)
            
            nodes = []
            edges = []
            node_ids = set()
            
            for record in result:
                role_name = record["role"]
                policy_name = record["policy"]
                permission_name = record["permission"]
                role_cloud = record["role_cloud"]
                
                # Add role node
                if role_name not in node_ids:
                    nodes.append({
                        "id": role_name,
                        "label": role_name,
                        "type": "Role",
                        "cloud": role_cloud
                    })
                    node_ids.add(role_name)
                
                # Add policy node
                policy_id = f"{role_name}:{policy_name}"
                if policy_id not in node_ids:
                    nodes.append({
                        "id": policy_id,
                        "label": policy_name,
                        "type": "Policy",
                        "cloud": role_cloud
                    })
                    node_ids.add(policy_id)
                
                # Add permission node
                if permission_name not in node_ids:
                    nodes.append({
                        "id": permission_name,
                        "label": permission_name,
                        "type": "Permission",
                        "cloud": role_cloud
                    })
                    node_ids.add(permission_name)
                
                # Add edges
                edges.append({
                    "source": role_name,
                    "target": policy_id,
                    "type": "HAS_POLICY"
                })
                edges.append({
                    "source": policy_id,
                    "target": permission_name,
                    "type": "ALLOWS"
                })
        
        client.close()
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    except Exception as e:
        logger.error(f"Error fetching graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk")
async def get_risk(cloud: Optional[str] = None):
    """Get risk scores for all roles."""
    try:
        cloud = _effective_cloud(cloud)
        risk_scores = batch_calculate_risk_scores(cloud=cloud)
        return {
            "roles": risk_scores,
            "summary": {
                "high": len([r for r in risk_scores if r.get("risk_level") == "high"]),
                "medium": len([r for r in risk_scores if r.get("risk_level") == "medium"]),
                "low": len([r for r in risk_scores if r.get("risk_level") == "low"]),
            },
        }
    except Exception as e:
        logger.error(f"Error fetching risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/escalation")
async def get_escalation(cloud: Optional[str] = None):
    """Get privilege escalation risks."""
    try:
        cloud = _effective_cloud(cloud)
        results = detect_all_escalation_risks(cloud=cloud)
        return {
            "direct_escalation": results.get("direct_escalation", []),
            "wildcard_permissions": results.get("wildcard_permissions", []),
        }
    except Exception as e:
        logger.error(f"Error fetching escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance")
async def get_compliance(cloud: Optional[str] = None):
    """Get compliance reports."""
    try:
        cloud = _effective_cloud(cloud)
        iso_report = generate_iso27001_report(cloud=cloud)
        nist_report = generate_nist80053_report(cloud=cloud)
        
        return {
            "iso27001": {
                "compliance_score": iso_report.get("compliance_score", 0),
                "non_compliant_controls": iso_report.get("non_compliant_controls", 0),
                "gaps": iso_report.get("compliance_gaps", [])
            },
            "nist80053": {
                "compliance_score": nist_report.get("compliance_score", 0),
                "non_compliant_controls": nist_report.get("non_compliant_controls", 0),
                "gaps": nist_report.get("compliance_gaps", [])
            }
        }
    except Exception as e:
        logger.error(f"Error fetching compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/llm/explain/{role_name}")
async def explain_role(role_name: str, cloud: Optional[str] = None):
    """Get LLM explanation for a role (with graceful fallback)."""
    try:
        cloud = _effective_cloud(cloud)
        risk_score = calculate_risk_score(role_name, cloud=cloud)
        escalation_results = detect_all_escalation_risks(cloud=cloud)
        role_escalation = [r for r in escalation_results.get("direct_escalation", []) if r["role"] == role_name]
        
        try:
            explanation = explain_risk(
                role_name=role_name,
                risk_score=risk_score.get("risk_score", 0),
                risk_level=risk_score.get("risk_level", "unknown"),
                escalation_findings=role_escalation,
                explainable_factors=risk_score.get("explainable_factors", {}),
            )
            if not explanation.get("llm_available"):
                return {
                    "role": role_name,
                    "message": explanation.get("message", "LLM not configured"),
                    "llm_available": False,
                }
            return {
                "role": role_name,
                "explanation": explanation.get("llm_explanation", "Explanation not available"),
                "llm_available": True,
            }
        except Exception as e:
            logger.warning(f"LLM explanation failed: {e}")
            return {
                "role": role_name,
                "message": "LLM not configured",
                "llm_available": False,
            }
    except Exception as e:
        logger.error(f"Error explaining role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
