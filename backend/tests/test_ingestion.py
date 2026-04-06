from backend.app.iam_ingestion.gcp import ingest_gcp_iam


def test_gcp_ingestion_graceful():
    result = ingest_gcp_iam()
    assert isinstance(result, list)

