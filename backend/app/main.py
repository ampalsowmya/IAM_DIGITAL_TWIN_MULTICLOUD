from typing import AsyncGenerator

import uvicorn
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .graph.neo4j_client import AsyncNeo4jClient, get_neo4j_client
from .api import auth as auth_router
from .api import ingestion as ingestion_router
from .api import graph as graph_router
from .api import risk as risk_router
from .api import whatif as whatif_router
from .api import llm as llm_router
from .api import compliance as compliance_router
from .api import remediation as remediation_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Multi-Cloud IAM Digital Twin API",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router.router, prefix="/api/v1")
    app.include_router(ingestion_router.router, prefix="/api/v1")
    app.include_router(graph_router.router, prefix="/api/v1")
    app.include_router(risk_router.router, prefix="/api/v1")
    app.include_router(whatif_router.router, prefix="/api/v1")
    app.include_router(llm_router.router, prefix="/api/v1")
    app.include_router(compliance_router.router, prefix="/api/v1")
    app.include_router(remediation_router.router, prefix="/api/v1")

    @app.get(
        "/api/v1/health",
        status_code=status.HTTP_200_OK,
        tags=["meta"],
        summary="Health check",
    )
    async def health(
        neo4j: AsyncNeo4jClient = Depends(get_neo4j_client),
    ) -> dict:
        """
        Health check endpoint.

        Example response:
        {
            "status": "ok",
            "neo4j": "up"
        }
        """

        neo4j_ok = await neo4j.health_check()
        return {"status": "ok", "neo4j": "up" if neo4j_ok else "down"}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )

"""
Multi-Cloud IAM Digital Twin - Main Application
===============================================
Production-grade academic project for IAM risk analysis across AWS, Azure, and GCP.

This is the main entry point that orchestrates:
1. Multi-cloud IAM ingestion
2. Graph database storage
3. Privilege escalation detection
4. What-if simulation
5. ML risk scoring
6. LLM governance explanations
7. Compliance mapping

Run this module to execute the complete IAM digital twin workflow.
"""
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('iam_digital_twin.log')
    ]
)

logger = logging.getLogger(__name__)

# Import modules
from .config import settings
from .iam_ingestion import run_aws_iam_ingestion
from .graph.escalation import detect_all_escalation_risks
from .simulation.what_if import run_what_if_simulation
from .ml.predict import batch_calculate_risk_scores
from .ml.train import train_all_models
from .llm.governance import explain_risk
from .compliance import generate_iso27001_report, generate_nist80053_report


def run_full_workflow(cloud: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute the complete IAM digital twin workflow.
    
    Workflow:
    1. Ingest IAM data from clouds
    2. Detect escalation risks
    3. Calculate ML risk scores
    4. Generate LLM explanations
    5. Map to compliance frameworks
    6. Generate comprehensive report
    
    Args:
        cloud: Optional cloud filter ("aws", "azure", "gcp")
        
    Returns:
        Complete workflow results dictionary
    """
    logger.info("=" * 60)
    logger.info("IAM DIGITAL TWIN - AWS-ONLY WORKFLOW")
    logger.info("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "cloud_filter": cloud,
        "ingestion": {},
        "escalation_detection": {},
        "risk_scoring": {},
        "llm_explanations": {},
        "compliance": {},
        "summary": {}
    }
    
    # Force AWS as default cloud for the workflow.
    cloud = cloud or settings.default_cloud or "aws"

    # Step 1: IAM Ingestion (AWS-only)
    logger.info("\n[1/6] IAM Data Ingestion (AWS)")
    logger.info("-" * 60)

    try:
        logger.info("Ingesting AWS IAM data...")
        aws_result = run_aws_iam_ingestion()
        results["ingestion"]["aws"] = aws_result
    except Exception as e:
        logger.error(f"AWS ingestion failed: {e}")
        results["ingestion"]["aws"] = {"status": "error", "error": str(e)}
    
    # Step 2: Escalation Detection
    logger.info("\n[2/6] Privilege Escalation Detection")
    logger.info("-" * 60)
    
    try:
        escalation_results = detect_all_escalation_risks(cloud=cloud)
        results["escalation_detection"] = escalation_results
        
        total_risky_roles = (
            len(escalation_results.get("direct_escalation", [])) +
            len(escalation_results.get("wildcard_permissions", []))
        )
        logger.info(f"Detected {total_risky_roles} roles with escalation risks")
    except Exception as e:
        logger.error(f"Escalation detection failed: {e}")
        results["escalation_detection"] = {"status": "error", "error": str(e)}
    
    # Step 3: ML Risk Scoring
    logger.info("\n[3/6] ML Risk Scoring")
    logger.info("-" * 60)
    
    try:
        # Train models if not already trained
        logger.info("Training/loading ML models...")
        train_all_models(cloud=cloud)
        
        # Calculate risk scores
        logger.info("Calculating risk scores...")
        risk_scores = batch_calculate_risk_scores(cloud=cloud)
        results["risk_scoring"] = {
            "total_roles": len(risk_scores),
            "high_risk": len([r for r in risk_scores if r.get("risk_level") == "high"]),
            "medium_risk": len([r for r in risk_scores if r.get("risk_level") == "medium"]),
            "low_risk": len([r for r in risk_scores if r.get("risk_level") == "low"]),
            "top_risky_roles": risk_scores[:10]  # Top 10
        }
        
        logger.info(f"Calculated risk scores for {len(risk_scores)} roles")
        logger.info(f"High risk: {results['risk_scoring']['high_risk']}, "
                   f"Medium: {results['risk_scoring']['medium_risk']}, "
                   f"Low: {results['risk_scoring']['low_risk']}")
    except Exception as e:
        logger.error(f"Risk scoring failed: {e}")
        results["risk_scoring"] = {"status": "error", "error": str(e)}
    
    # Step 4: LLM Explanations (for top risky roles)
    logger.info("\n[4/6] LLM Governance Explanations")
    logger.info("-" * 60)
    
    try:
        top_risky = results["risk_scoring"].get("top_risky_roles", [])[:5]  # Top 5
        llm_explanations = []
        
        for role_score in top_risky:
            role_name = role_score.get("role")
            if role_name:
                logger.info(f"Generating LLM explanation for {role_name}...")
                explanation = explain_risk(
                    role_name=role_name,
                    risk_score=role_score.get("risk_score", 0),
                    risk_level=role_score.get("risk_level", "unknown"),
                    escalation_findings=escalation_results.get("direct_escalation", []),
                    explainable_factors=role_score.get("explainable_factors", {})
                )
                llm_explanations.append(explanation)
        
        results["llm_explanations"] = {
            "total_explained": len(llm_explanations),
            "explanations": llm_explanations
        }
        logger.info(f"Generated {len(llm_explanations)} LLM explanations")
    except Exception as e:
        logger.error(f"LLM explanations failed: {e}")
        results["llm_explanations"] = {"status": "error", "error": str(e)}
    
    # Step 5: Compliance Mapping
    logger.info("\n[5/6] Compliance Mapping")
    logger.info("-" * 60)
    
    try:
        logger.info("Generating ISO 27001 compliance report...")
        iso27001_report = generate_iso27001_report(cloud=cloud)
        results["compliance"]["iso27001"] = iso27001_report
        
        logger.info("Generating NIST SP 800-53 compliance report...")
        nist80053_report = generate_nist80053_report(cloud=cloud)
        results["compliance"]["nist80053"] = nist80053_report
        
        logger.info(f"ISO 27001 Compliance: {iso27001_report.get('compliance_score', 0)}%")
        logger.info(f"NIST 800-53 Compliance: {nist80053_report.get('compliance_score', 0)}%")
    except Exception as e:
        logger.error(f"Compliance mapping failed: {e}")
        results["compliance"] = {"status": "error", "error": str(e)}
    
    # Step 6: Summary
    logger.info("\n[6/6] Generating Summary")
    logger.info("-" * 60)
    
    results["summary"] = {
        "total_roles_analyzed": results["risk_scoring"].get("total_roles", 0),
        "escalation_risks": len(escalation_results.get("direct_escalation", [])),
        "wildcard_risks": len(escalation_results.get("wildcard_permissions", [])),
        "high_risk_roles": results["risk_scoring"].get("high_risk", 0),
        "iso27001_compliance": results["compliance"].get("iso27001", {}).get("compliance_score", 0),
        "nist80053_compliance": results["compliance"].get("nist80053", {}).get("compliance_score", 0),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Summary: {results['summary']}")
    
    return results


def run_quick_analysis(role_name: str, cloud: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick analysis for a single role.
    
    Args:
        role_name: Role to analyze
        cloud: Optional cloud filter
        
    Returns:
        Analysis results for the role
    """
    logger.info(f"Quick analysis for role: {role_name}")
    
    from .ml.predict import calculate_risk_score
    from .graph.escalation import detect_privilege_escalation
    from .llm.governance import explain_risk
    
    # Get risk score
    risk_score = calculate_risk_score(role_name, cloud=cloud)
    
    # Get escalation findings
    escalation_findings = detect_privilege_escalation(cloud=cloud)
    role_escalation = [f for f in escalation_findings if f["role"] == role_name]
    
    # Get LLM explanation
    explanation = explain_risk(
        role_name=role_name,
        risk_score=risk_score.get("risk_score", 0),
        risk_level=risk_score.get("risk_level", "unknown"),
        escalation_findings=role_escalation,
        explainable_factors=risk_score.get("explainable_factors", {})
    )
    
    return {
        "role": role_name,
        "risk_score": risk_score,
        "escalation_findings": role_escalation,
        "llm_explanation": explanation
    }


if __name__ == "__main__":
    import argparse
    import os
    
    # Check if running as API server (via uvicorn)
    if os.getenv("RUN_AS_API", "").lower() == "true" or "uvicorn" in str(sys.argv[0]):
        # Run as API server
        import uvicorn
        uvicorn.run("backend.app.api:app", host="0.0.0.0", port=8000)
    else:
        # Run as CLI
        parser = argparse.ArgumentParser(description="Multi-Cloud IAM Digital Twin")
        parser.add_argument(
            "--cloud",
            choices=["aws", "azure", "gcp"],
            help="Filter analysis to specific cloud"
        )
        parser.add_argument(
            "--role",
            help="Quick analysis for specific role"
        )
        parser.add_argument(
            "--train-only",
            action="store_true",
            help="Only train ML models, don't run full workflow"
        )
        parser.add_argument(
            "--api",
            action="store_true",
            help="Run as API server"
        )
        
        args = parser.parse_args()
        
        if args.api:
            import uvicorn
            uvicorn.run("backend.app.api:app", host="0.0.0.0", port=8000)
        elif args.train_only:
            logger.info("Training ML models only...")
            train_all_models(cloud=args.cloud)
        elif args.role:
            results = run_quick_analysis(args.role, cloud=args.cloud)
            print("\n=== QUICK ANALYSIS RESULTS ===")
            print(f"Role: {results['role']}")
            print(f"Risk Score: {results['risk_score'].get('risk_score', 0)}/100")
            print(f"Risk Level: {results['risk_score'].get('risk_level', 'unknown')}")
            if results['escalation_findings']:
                print(f"Escalation Risks: {results['escalation_findings']}")
            if results['llm_explanation'].get('llm_available'):
                print(f"\nLLM Explanation:\n{results['llm_explanation'].get('llm_explanation', 'N/A')}")
        else:
            results = run_full_workflow(cloud=args.cloud)
            print("\n=== WORKFLOW RESULTS ===")
            print(f"Summary: {results['summary']}")
