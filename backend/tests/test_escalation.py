from backend.app.graph.escalation import ESCALATION_QUERY


def test_escalation_query_exists():
    assert "MATCH path" in ESCALATION_QUERY

