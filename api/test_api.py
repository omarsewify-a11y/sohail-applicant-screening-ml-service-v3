"""
Automated test suite for the Sohail Applicant Screening API (v3).

Run with:
    pytest -v

Covers /health, /predict (good + bad input), /predict-batch (good + bad input),
and /results.
"""

import io
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Use isolated, disposable paths so tests never touch the real shared log
os.environ["LOG_PATH"] = "./test_predictions_log.csv"
os.environ.setdefault("MODEL_PATH", "../data_training/model_v3.joblib")

sys.path.insert(0, os.path.dirname(__file__))
from main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_log():
    yield
    if os.path.exists("./test_predictions_log.csv"):
        os.remove("./test_predictions_log.csv")


# ── /health ──────────────────────────────────────────────────────────────
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


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


# ── /predict — bad input ────────────────────────────────────────────────
def test_predict_gpa_out_of_range():
    """GPA above the valid 0.0-4.0 range should be rejected, not crash the service."""
    payload = {"gpa": 9.9, "skills_count": 5, "prior_projects": 2, "track": "AI"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body


def test_predict_invalid_track():
    """A track outside {AI, Data, Web} should be rejected cleanly."""
    payload = {"gpa": 3.0, "skills_count": 5, "prior_projects": 2, "track": "Marketing"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body


def test_predict_missing_field():
    """A missing required field should return 422, not a server crash."""
    payload = {"gpa": 3.0, "skills_count": 5, "track": "AI"}  # missing prior_projects
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_wrong_type():
    """A non-numeric gpa should be rejected cleanly."""
    payload = {"gpa": "not-a-number", "skills_count": 5, "prior_projects": 2, "track": "AI"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


# ── /predict-batch — good input ─────────────────────────────────────────
def test_predict_batch_valid_csv():
    csv_content = (
        "gpa,skills_count,prior_projects,track\n"
        "3.8,8,5,AI\n"
        "2.1,1,0,Web\n"
        "3.6,6,4,Data\n"
    )
    files = {"file": ("batch.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 3
    assert body["successful"] == 3
    assert body["failed"] == 0
    assert len(body["results"]) == 3


# ── /predict-batch — bad input ──────────────────────────────────────────
def test_predict_batch_missing_columns():
    csv_content = "gpa,skills_count\n3.8,8\n"
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
    """Rows with bad values inside an otherwise valid CSV are reported, not crashed on."""
    csv_content = (
        "gpa,skills_count,prior_projects,track\n"
        "3.8,8,5,AI\n"
        "9.9,2,1,Web\n"  # invalid gpa
        "3.0,4,2,Robotics\n"  # invalid track
    )
    files = {"file": ("mixed.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/predict-batch", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["successful"] == 1
    assert body["failed"] == 2


# ── /results ─────────────────────────────────────────────────────────────
def test_results_dashboard_loads():
    response = client.get("/results")
    assert response.status_code == 200
    assert "Results Dashboard" in response.text
