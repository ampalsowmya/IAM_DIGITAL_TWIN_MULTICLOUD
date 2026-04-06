RISK_EXPLAIN_PROMPT = """
Given role {name}, risk score {score}, permissions {perms},
explain risk in plain English in at most 3 bullet points.
"""

POLICY_RECOMMEND_PROMPT = """
Given excessive permissions {perms}, suggest least-privilege policy JSON.
Return only JSON.
"""

COMPLIANCE_GAP_PROMPT = """
Given IAM state summary {summary}, list major gaps against {framework} controls.
Return concise bullets.
"""

