"""
Sohail Applicant Screening API — v3
Deployment, Testing & Reliability layer (Easa Nazir)

Loads Khaled's frozen model_v3.joblib and serves predictions.
Every prediction is appended to the shared predictions_log.csv that
Omar's monitoring layer reads from.
"""

import os
import io
import csv
import logging
from datetime import datetime, timezone
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("applicant-screening-api")

# ── Configuration (env-overridable for local dev vs. Docker) ───────────────
MODEL_PATH = os.getenv("MODEL_PATH", "../data_training/model_v3.joblib")
LOG_FILE = os.getenv("LOG_PATH", "../monitoring/predictions_log.csv")

LOG_COLUMNS = ["timestamp", "gpa", "skills_count", "prior_projects", "track",
               "experience_score", "high_gpa", "prediction", "confidence"]

# ── Load Khaled's frozen v3 Pipeline — never retrain here ──────────────────
try:
    model = joblib.load(MODEL_PATH)
    logger.info(f"Loaded model from {MODEL_PATH}")
except FileNotFoundError as e:
    raise RuntimeError(
        f"Could not find model file at '{MODEL_PATH}'. "
        f"Set the MODEL_PATH environment variable or check data_training/model_v3.joblib exists."
    ) from e

# Ensure the shared log file (and its directory) exist with the correct header
os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        writer.writeheader()

app = FastAPI(
    title="Sohail Applicant Screening API",
    description="v3 — Deployed, tested, and hardened API for internship applicant screening.",
    version="3.0.0"
)


# ── Schemas ──────────────────────────────────────────────────────────────
class ApplicantInput(BaseModel):
    gpa: float = Field(..., ge=0.0, le=4.0, description="Applicant GPA (0.0 - 4.0)")
    skills_count: int = Field(..., ge=0, description="Number of technical skills")
    prior_projects: int = Field(..., ge=0, description="Number of completed projects")
    track: Literal["AI", "Data", "Web"] = Field(..., description="Internship track: AI, Data, or Web")


class PredictionOutput(BaseModel):
    prediction: str
    confidence: float


class ErrorResponse(BaseModel):
    error: str
    detail: str


# ── Global error handlers (hardened error responses) ───────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a clean 422 instead of FastAPI's raw stack of pydantic errors."""
    messages = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        messages.append(f"{field}: {err['msg']}")
    logger.warning(f"Validation error on {request.url.path}: {messages}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Invalid input", "detail": "; ".join(messages)}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all so the service never returns a bare 500 traceback to a client."""
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": "Something went wrong while processing the request."}
    )


# ── Core prediction logic (shared by /predict and /predict-batch) ──────────
def engineer_features(gpa: float, skills_count: int, prior_projects: int) -> dict:
    """Compute the two engineered features expected by Khaled's v3 Pipeline."""
    return {
        "experience_score": skills_count + prior_projects,
        "high_gpa": 1 if gpa >= 3.5 else 0
    }


def run_prediction(gpa, skills_count, prior_projects, track):
    """Run prediction through Khaled's frozen v3 Pipeline and return label + confidence."""
    eng = engineer_features(gpa, skills_count, prior_projects)
    features = pd.DataFrame([{
        "gpa": gpa,
        "skills_count": skills_count,
        "prior_projects": prior_projects,
        "experience_score": eng["experience_score"],
        "high_gpa": eng["high_gpa"],
        "track": track
    }])
    prediction_int = model.predict(features)[0]
    confidence = float(max(model.predict_proba(features)[0]))
    label = "Shortlisted" if prediction_int == 1 else "Review Later"
    return label, round(confidence, 4), eng


def log_prediction(gpa, skills_count, prior_projects, track, eng, label, confidence):
    """Append one prediction row to the shared predictions_log.csv used by Omar's monitoring."""
    row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "gpa": gpa,
        "skills_count": skills_count,
        "prior_projects": prior_projects,
        "track": track,
        "experience_score": eng["experience_score"],
        "high_gpa": eng["high_gpa"],
        "prediction": label,
        "confidence": confidence
    }
    try:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
            writer.writerow(row)
    except OSError as e:
        # Logging failure should never take the API down — just report it.
        logger.error(f"Could not write to prediction log at {LOG_FILE}: {e}")


# ── Endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Sohail Applicant Screening API v3 is running."}


@app.post("/predict", response_model=PredictionOutput, responses={422: {"model": ErrorResponse}})
def predict(applicant: ApplicantInput):
    """Single applicant prediction."""
    try:
        label, confidence, eng = run_prediction(
            applicant.gpa, applicant.skills_count, applicant.prior_projects, applicant.track
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Prediction failed", "detail": "The model could not score this applicant."}
        )
    log_prediction(applicant.gpa, applicant.skills_count, applicant.prior_projects,
                   applicant.track, eng, label, confidence)
    return PredictionOutput(prediction=label, confidence=confidence)


@app.post("/predict-batch", responses={400: {"model": ErrorResponse}})
async def predict_batch(file: UploadFile = File(...)):
    """
    Batch prediction from a CSV file.
    CSV must have columns: gpa, skills_count, prior_projects, track
    Returns predictions for all valid rows and reports any rows that failed.
    """
    if not file.filename.lower().endswith(".csv"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid file type", "detail": "Please upload a .csv file."}
        )

    contents = await file.read()
    if not contents:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Empty file", "detail": "The uploaded CSV file has no content."}
        )

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Unreadable CSV", "detail": "The file could not be parsed as a valid CSV."}
        )

    required_cols = {"gpa", "skills_count", "prior_projects", "track"}
    missing = required_cols - set(df.columns)
    if missing:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Missing columns", "detail": f"CSV is missing required columns: {sorted(missing)}"}
        )

    if len(df) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "No rows", "detail": "The CSV file has headers but no data rows."}
        )

    results = []
    errors = []
    valid_tracks = {"AI", "Data", "Web"}

    for idx, row in df.iterrows():
        try:
            gpa = float(row["gpa"])
            skills_count = int(row["skills_count"])
            prior_projects = int(row["prior_projects"])
            track = str(row["track"])

            if not (0.0 <= gpa <= 4.0):
                raise ValueError(f"gpa {gpa} out of range 0.0-4.0")
            if skills_count < 0 or prior_projects < 0:
                raise ValueError("skills_count and prior_projects must be >= 0")
            if track not in valid_tracks:
                raise ValueError(f"track '{track}' must be one of {sorted(valid_tracks)}")

            label, confidence, eng = run_prediction(gpa, skills_count, prior_projects, track)
            log_prediction(gpa, skills_count, prior_projects, track, eng, label, confidence)

            results.append({
                "row": int(idx),
                "gpa": gpa,
                "skills_count": skills_count,
                "prior_projects": prior_projects,
                "track": track,
                "experience_score": eng["experience_score"],
                "high_gpa": eng["high_gpa"],
                "prediction": label,
                "confidence": confidence
            })
        except (ValueError, TypeError, KeyError) as e:
            errors.append({"row": int(idx), "error": str(e)})

    shortlisted = sum(1 for r in results if r["prediction"] == "Shortlisted")
    review_later = len(results) - shortlisted

    return {
        "total_rows": len(df),
        "successful": len(results),
        "failed": len(errors),
        "shortlisted": shortlisted,
        "review_later": review_later,
        "results": results,
        "errors": errors
    }


@app.get("/results", response_class=HTMLResponse)
def results_dashboard():
    """Simple HTML dashboard showing the latest predictions from the shared log."""
    if not os.path.exists(LOG_FILE):
        rows = []
    else:
        try:
            df = pd.read_csv(LOG_FILE)
            rows = df.tail(50).to_dict(orient="records")
        except Exception as e:
            logger.error(f"Could not read log file for dashboard: {e}")
            rows = []

    total = len(rows)
    shortlisted = sum(1 for r in rows if r.get("prediction") == "Shortlisted")
    review_later = total - shortlisted
    avg_conf = round(sum(r.get("confidence", 0) for r in rows) / total, 4) if total > 0 else 0

    rows_html = ""
    for r in reversed(rows):
        badge_color = "#22c55e" if r.get("prediction") == "Shortlisted" else "#f59e0b"
        rows_html += f"""
        <tr>
            <td>{r.get('timestamp', '')}</td>
            <td>{r.get('gpa', '')}</td>
            <td>{r.get('skills_count', '')}</td>
            <td>{r.get('prior_projects', '')}</td>
            <td>{r.get('track', '')}</td>
            <td>{r.get('experience_score', '')}</td>
            <td>{r.get('high_gpa', '')}</td>
            <td><span style="background:{badge_color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.85em">{r.get('prediction', '')}</span></td>
            <td>{r.get('confidence', '')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sohail Applicant Screening — Results Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #f1f5f9; color: #1e293b; }}
  header {{ background: #1e3a5f; color: white; padding: 24px 32px; }}
  header h1 {{ font-size: 1.5rem; }}
  header p {{ font-size: 0.9rem; opacity: 0.75; margin-top: 4px; }}
  .stats {{ display: flex; gap: 16px; padding: 24px 32px; flex-wrap: wrap; }}
  .card {{ background: white; border-radius: 10px; padding: 20px 28px; flex: 1; min-width: 160px;
           box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .card .label {{ font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
  .card .value {{ font-size: 2rem; font-weight: 700; margin-top: 4px; }}
  .card.green .value {{ color: #16a34a; }}
  .card.amber .value {{ color: #d97706; }}
  .card.blue .value {{ color: #2563eb; }}
  .card.slate .value {{ color: #475569; }}
  .table-wrap {{ padding: 0 32px 32px; overflow-x: auto; }}
  h2 {{ font-size: 1rem; color: #475569; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; background: white;
           border-radius: 10px; overflow: hidden;
           box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  th {{ background: #1e3a5f; color: white; padding: 12px 14px; text-align: left;
        font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  td {{ padding: 11px 14px; font-size: 0.88rem; border-bottom: 1px solid #f1f5f9; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f8fafc; }}
</style>
</head>
<body>
<header>
  <h1>Sohail Applicant Screening — Results Dashboard</h1>
  <p>v3 Deployed API &nbsp;|&nbsp; Showing latest {min(total, 50)} predictions</p>
</header>
<div class="stats">
  <div class="card slate"><div class="label">Total Predictions</div><div class="value">{total}</div></div>
  <div class="card green"><div class="label">Shortlisted</div><div class="value">{shortlisted}</div></div>
  <div class="card amber"><div class="label">Review Later</div><div class="value">{review_later}</div></div>
  <div class="card blue"><div class="label">Avg Confidence</div><div class="value">{avg_conf}</div></div>
</div>
<div class="table-wrap">
  <h2>Prediction Log</h2>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th><th>GPA</th><th>Skills</th><th>Projects</th>
        <th>Track</th><th>Exp Score</th><th>High GPA</th><th>Prediction</th><th>Confidence</th>
      </tr>
    </thead>
    <tbody>{rows_html if rows_html else '<tr><td colspan="9" style="text-align:center;color:#94a3b8;padding:32px">No predictions yet. Run /predict or /predict-batch to get started.</td></tr>'}</tbody>
  </table>
</div>
</body>
</html>"""
    return HTMLResponse(content=html)
