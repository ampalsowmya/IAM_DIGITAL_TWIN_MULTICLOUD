from backend.app.ml.synthetic_data import generate_synthetic_iam_data


def test_synthetic_rows():
    df = generate_synthetic_iam_data(100)
    assert len(df) == 100
    assert "high_risk" in df.columns

