"""
What-If Simulation Engine
========================
This module provides "what-if" analysis for IAM changes.

Key Features:
1. Simulate permission removal without modifying live cloud resources
2. Recompute escalation risk after simulated changes
3. Compare before vs after risk scores
4. Generate remediation recommendations

IMPORTANT: All simulations run ONLY on the graph - never modify AWS/Azure directly.
"""
import logging
from typing import List, Dict, Any, Optional, Set
from ..graph.neo4j_client import Neo4jClient
from ..graph.escalation import detect_privilege_escalation, detect_wildcard_permissions, ALL_ESCALATION_PERMISSIONS
from ..ml.predict import calculate_risk_score

logger = logging.getLogger(__name__)


class WhatIfSimulator:
    """
    What-if simulation engine for IAM changes.
    Runs simulations on graph data without modifying cloud resources.
    """
    
    def __init__(self):
        self.client = Neo4jClient()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def get_current_state(self, role_name: Optional[str] = None, cloud: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current state of escalation risks.
        
        Args:
            role_name: Optional specific role to analyze
            cloud: Optional cloud filter
            
        Returns:
            Current state dictionary with escalation findings
        """
        escalation_findings = detect_privilege_escalation(cloud=cloud)
        wildcard_findings = detect_wildcard_permissions(cloud=cloud)
        
        if role_name:
            escalation_findings = [f for f in escalation_findings if f["role"] == role_name]
            wildcard_findings = [f for f in wildcard_findings if f["role"] == role_name]
        
        return {
            "escalation_risks": escalation_findings,
            "wildcard_risks": wildcard_findings,
            "total_risky_roles": len(escalation_findings) + len(wildcard_findings)
        }
    
    def simulate_permission_removal(
        self,
        role_name: str,
        permissions_to_remove: List[str],
        cloud: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate removing permissions from a role.
        This runs ONLY on the graph - does not modify AWS/Azure.
        
        Args:
            role_name: Role to simulate changes on
            permissions_to_remove: List of permissions to remove
            cloud: Optional cloud filter
            
        Returns:
            Simulation results with before/after comparison
        """
        logger.info(f"Simulating permission removal for {role_name}: {permissions_to_remove}")
        
        # Get current state
        current_state = self.get_current_state(role_name=role_name, cloud=cloud)
        
        # Simulate: Query graph excluding the removed permissions
        if cloud:
            query = """
            MATCH (r:Role {name: $role_name, cloud: $cloud})-[:HAS_POLICY]->(:Policy)-[:HAS_PERMISSION]->(p:Permission)
            WHERE p.name IN $dangerous_permissions
              AND NOT p.name IN $excluded_permissions
            RETURN r.name AS role, collect(DISTINCT p.name) AS remaining_risky_permissions
            """
        else:
            query = """
            MATCH (r:Role {name: $role_name})-[:HAS_POLICY]->(:Policy)-[:HAS_PERMISSION]->(p:Permission)
            WHERE p.name IN $dangerous_permissions
              AND NOT p.name IN $excluded_permissions
            RETURN r.name AS role, collect(DISTINCT p.name) AS remaining_risky_permissions
            """
        
        with self.client.driver.session() as session:
            result = session.run(
                query,
                role_name=role_name,
                cloud=cloud,
                dangerous_permissions=ALL_ESCALATION_PERMISSIONS,
                excluded_permissions=permissions_to_remove
            )
            
            simulated_findings = []
            for record in result:
                simulated_findings.append({
                    "role": record["role"],
                    "remaining_risky_permissions": record["remaining_risky_permissions"]
                })
        
        # Calculate risk reduction
        before_count = len([f for f in current_state["escalation_risks"] if f["role"] == role_name])
        after_count = len(simulated_findings)
        risk_reduction = before_count - after_count
        
        return {
            "role": role_name,
            "permissions_removed": permissions_to_remove,
            "before": {
                "escalation_risks": [f for f in current_state["escalation_risks"] if f["role"] == role_name],
                "risk_count": before_count
            },
            "after": {
                "escalation_risks": simulated_findings,
                "risk_count": after_count
            },
            "risk_reduction": risk_reduction,
            "recommendation": "SAFE TO REMOVE" if risk_reduction > 0 else "REVIEW REQUIRED"
        }
    
    def simulate_policy_removal(
        self,
        role_name: str,
        policy_name: str,
        cloud: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate removing an entire policy from a role.
        
        Args:
            role_name: Role to simulate changes on
            policy_name: Policy to remove
            cloud: Optional cloud filter
            
        Returns:
            Simulation results
        """
        logger.info(f"Simulating policy removal: {role_name} -> {policy_name}")
        
        # Get permissions in the policy
        if cloud:
            query = """
            MATCH (r:Role {name: $role_name, cloud: $cloud})-[:HAS_POLICY]->(p:Policy {name: $policy_name})-[:HAS_PERMISSION]->(perm:Permission)
            RETURN collect(DISTINCT perm.name) AS permissions
            """
        else:
            query = """
            MATCH (r:Role {name: $role_name})-[:HAS_POLICY]->(p:Policy {name: $policy_name})-[:HAS_PERMISSION]->(perm:Permission)
            RETURN collect(DISTINCT perm.name) AS permissions
            """
        
        with self.client.driver.session() as session:
            result = session.run(query, role_name=role_name, policy_name=policy_name, cloud=cloud)
            record = result.single()
            permissions_in_policy = record["permissions"] if record else []
        
        # Simulate removal
        return self.simulate_permission_removal(
            role_name=role_name,
            permissions_to_remove=permissions_in_policy,
            cloud=cloud
        )
    
    def compare_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple what-if scenarios.
        
        Args:
            scenarios: List of scenario dictionaries
                Each scenario: {"name": "scenario1", "permissions_to_remove": [...]}
        
        Returns:
            Comparison results
        """
        comparison = {
            "scenarios": [],
            "best_scenario": None,
            "max_risk_reduction": 0
        }
        
        for scenario in scenarios:
            result = self.simulate_permission_removal(
                role_name=scenario["role_name"],
                permissions_to_remove=scenario["permissions_to_remove"],
                cloud=scenario.get("cloud")
            )
            
            scenario_result = {
                "name": scenario["name"],
                "risk_reduction": result["risk_reduction"],
                "remaining_risks": result["after"]["risk_count"]
            }
            
            comparison["scenarios"].append(scenario_result)
            
            if result["risk_reduction"] > comparison["max_risk_reduction"]:
                comparison["max_risk_reduction"] = result["risk_reduction"]
                comparison["best_scenario"] = scenario["name"]
        
        return comparison


def run_what_if_simulation(role_name: Optional[str] = None):
    """
    Example what-if simulation workflow.
    
    Args:
        role_name: Optional specific role to simulate
    """
    print("\n=== WHAT-IF SIMULATION ENGINE ===\n")
    
    with WhatIfSimulator() as simulator:
        # Get current state
        print("--- CURRENT STATE ---")
        current = simulator.get_current_state(role_name=role_name)
        print(f"Total risky roles: {current['total_risky_roles']}")
        
        if current["escalation_risks"]:
            print("\nEscalation risks:")
            for risk in current["escalation_risks"][:5]:  # Show first 5
                print(f"  - {risk['role']} ({risk['cloud']}): {risk['risky_permissions']}")
        
        # Simulate permission removal
        if current["escalation_risks"]:
            example_role = current["escalation_risks"][0]
            print(f"\n--- SIMULATING: Remove permissions from {example_role['role']} ---")
            
            simulation = simulator.simulate_permission_removal(
                role_name=example_role["role"],
                permissions_to_remove=example_role["risky_permissions"][:1]  # Remove first risky permission
            )
            
            print(f"Before: {simulation['before']['risk_count']} risks")
            print(f"After: {simulation['after']['risk_count']} risks")
            print(f"Risk reduction: {simulation['risk_reduction']}")
            print(f"Recommendation: {simulation['recommendation']}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    run_what_if_simulation()
