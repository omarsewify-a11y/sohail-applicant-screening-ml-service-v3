"""
Automated test suite for the Sohail Applicant Screening API (v4).

Run with:
    pytest -v

Covers /health, /predict (good + bad input + validation integration),
/predict-batch (good + bad input + size limits), /results, /performance,
and security hardening (safe errors, no secret leakage).
"""

import io
import os
import sys
import json

import pytest
from fastapi.testclient import TestClient

# Use isolated, disposable paths so tests never touch the real shared log
os.environ["LOG_PATH"] = "./test_predictions_log_v4.csv"
os.environ.setdefault("MODEL_PATH", "../data_training/model_v3.joblib")

sys.path.insert(0, os.path.dirname(__file__))
from main_v4 import app, validate_input  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_log():
    yield
    if os.path.exists("./test_predictions_log_v4.csv"):
        os.remove("./test_predictions_log_v4.csv")


# ── validate_input integration tests ─────────────────────────────────────
def test_validate_input_valid():
    record = {"gpa": 3.5, "skills_count": 5, "prior_projects": 2, "track": "AI"}
    is_valid, result = validate_input(record)
    assert is_valid is True
    assert result["gpa"] == 3.5
    assert result["skills_count"] == 5


def test_validate_input_missing_field():
    record = {"gpa": 3.5, "skills_count": 5, "track": "AI"}  # missing prior_projects
    is_valid, result = validate_input(record)
    assert is_valid is False
    assert "Missing field" in result


def test_validate_input_gpa_out_of_range():
    record = {"gpa": 5.0, "skills_count": 5, "prior_projects": 2, "track": "AI"}
    is_valid, result = validate_input(record)
    assert is_valid is False
    assert "GPA" in result


def test_validate_input_negative_skills():
    record = {"gpa": 3.0, "skills_count": -1, "prior_projects": 2, "track": "AI"}
    is_valid, result = validate_input(record)
    assert is_valid is False
    assert "skills_count" in result


def test_validate_input_unknown_track():
    record = {"gpa": 3.0, "skills_count": 5, "prior_projects": 2, "track": "Marketing"}
    is_valid, result = validate_input(record)
    assert is_valid is False
    assert "track" in result


def test_validate_input_float_whole_number():
    """API JSON sends whole-number floats; validator should accept them."""
    record = {"gpa": 3.0, "skills_count": 5.0, "prior_projects": 2.0, "track": "AI"}
    is_valid, result = validate_input(record)
    assert is_valid is True
    assert result["skills_count"] == 5
    assert result["prior_projects"] == 2


# ── /health ──────────────────────────────────────────────────────────────
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "v4" in body["version"]


# ── /predict — good input ───────────────────────────────────────────────
def test_predict_valid_applicant():
    payload = {"gpa": 3.8, "skills_count": 8, "prior_projects": 5, "track": "AI"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] in ["Shortlisted", "Review Later"]
    assert 0.0 <= body["confidence"] <= 1.0


def test_predict_valid_low_scoring_applicant():
    payload = {"gpa": 2.0, "skills_count": 0, "prior_projects": 0, "track": "Web"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] in ["Shortlisted", "Review Later"]


# ── /predict — bad input (security hardening) ────────────────────────────
def test_predict_gpa_out_of_range():
    payload = {"gpa": 9.9, "skills_count": 5, "prior_projects": 2, "track": "AI"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert "detail" in body
    # Security: no stack trace or internal paths leaked
    assert "traceback" not in json.dumps(body).lower()
    assert "model_v3" not in json.dumps(body).lower()


def test_predict_invalid_track():
    payload = {"gpa": 3.0, "skills_count": 5, "prior_projects": 2, "track": "Marketing"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body


def test_predict_missing_field():
    payload = {"gpa": 3.0, "skills_count": 5, "track": "AI"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_wrong_type():
    payload = {"gpa": "not-a-number", "skills_count": 5, "prior_projects": 2, "track": "AI"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


# ── /predict — safe error messages (no secret leakage) ───────────────────
def test_predict_safe_error_no_secrets():
    """Ensure error responses never contain file paths, model names, or internal details."""
    payload = {"gpa": 99, "skills_count": 5, "prior_projects": 2, "track": "AI"}
    response = client.post("/predict", json=payload)
    body = response.json()
    response_text = json.dumps(body).lower()
    forbidden = ["model_v3", "joblib", "data_training", "predictions_log", "../", "/app/"]
    for term in forbidden:
        assert term not in response_text, f"Secret leaked in error: {term}"


# ── /predict-batch — good input ─────────────────────────────────────────
def test_predict_batch_valid_csv():
    csv_content = (
        "gpa,skills_count,prior_projects,track
"
        "3.8,8,5,AI
"
        "2.1,1,0,Web
"
        "3.6,6,4,Data
"
    )
    files = {"file": ("batch.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 3
    assert body["successful"] == 3
    assert body["failed"] == 0


# ── /predict-batch — bad input ──────────────────────────────────────────
def test_predict_batch_missing_columns():
    csv_content = "gpa,skills_count
3.8,8
"
    files = {"file": ("bad.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 400
    body = response.json()
    assert "error" in body


def test_predict_batch_wrong_file_type():
    files = {"file": ("notes.txt", io.BytesIO(b"this is not a csv"), "text/plain")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 400


def test_predict_batch_empty_file():
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 400


def test_predict_batch_partial_bad_rows():
    csv_content = (
        "gpa,skills_count,prior_projects,track
"
        "3.8,8,5,AI
"
        "9.9,2,1,Web
"
        "3.0,4,2,Robotics
"
    )
    files = {"file": ("mixed.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["successful"] == 1
    assert body["failed"] == 2


# ── /predict-batch — size limits (security) ──────────────────────────────
def test_predict_batch_too_many_rows():
    """CSV with >500 rows should be rejected with 413."""
    header = "gpa,skills_count,prior_projects,track
"
    rows = "3.5,5,2,AI
" * 501
    csv_content = header + rows
    files = {"file": ("huge.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 413
    body = response.json()
    assert "Too many rows" in body["detail"]


def test_predict_batch_oversized_file():
    """CSV file >2 MB should be rejected with 413."""
    header = "gpa,skills_count,prior_projects,track
"
    # Create a ~3 MB file
    rows = "3.5,5,2,AI," + "x" * 1000 + "
" * 3000
    csv_content = header + rows
    files = {"file": ("big.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 413
    body = response.json()
    assert "File too large" in body["detail"]


# ── /results ─────────────────────────────────────────────────────────────
def test_results_dashboard_loads():
    response = client.get("/results")
    assert response.status_code == 200
    assert "Results Dashboard" in response.text


def test_results_dashboard_has_v4_branding():
    response = client.get("/results")
    assert "v4" in response.text


# ── /performance ─────────────────────────────────────────────────────────
def test_performance_endpoint_exists():
    response = client.get("/performance")
    assert response.status_code == 200
    body = response.json()
    assert "measurements" in body
    assert "summary" in body
