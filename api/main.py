"""
Sohail Applicant Screening API — v4 (Productization & Quality Hardening)
Owner: Easa Nazir (API Hardening, Security & User Experience)

v4 Changes:
- Integrated Khaled's validate_input() for unified validation
- Security hardening: input size limits, safe error responses, secret scrubbing
- Performance measurement: response-time tracking for all endpoints
- Improved user experience: cleaner results dashboard
- Coordinated with Omar on log format for monitoring compatibility
"""

import os
import io
import csv
import time
import logging
from datetime import datetime, timezone
from typing import Literal
from contextlib import contextmanager

import joblib
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# ── Import Khaled's reusable validator ───────────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../data_training"))
from validation import validate_input

# ── Logging (never leak internals) ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("applicant-screening-api")

# ── Configuration (env-overridable, secrets never exposed) ───────────────
MODEL_PATH = os.getenv("MODEL_PATH", "../data_training/model_v3.joblib")
LOG_FILE = os.getenv("LOG_PATH", "../monitoring/predictions_log.csv")

# Security limits
MAX_REQUEST_SIZE_MB = 5           # Reject body > 5 MB
MAX_BATCH_ROWS = 500              # Reject CSV with > 500 rows
MAX_BATCH_FILE_SIZE_MB = 2        # Reject batch file > 2 MB

LOG_COLUMNS = [
    "timestamp", "gpa", "skills_count", "prior_projects", "track",
    "experience_score", "high_gpa", "prediction", "confidence"
]

# ── Performance tracking ─────────────────────────────────────────────────
performance_log = []  # In-memory; written to PERFORMANCE.md on demand


@contextmanager
def timed_operation(operation_name: str):
    """Context manager to record response time for an operation."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        performance_log.append({
            "operation": operation_name,
            "response_time_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"[PERF] {operation_name}: {elapsed_ms} ms")


# ── Load Khaled's frozen v3 Pipeline — never retrain here ────────────────
try:
    with timed_operation("model_load"):
        model = joblib.load(MODEL_PATH)
    logger.info(f"Loaded model from {MODEL_PATH}")
except FileNotFoundError as e:
    raise RuntimeError(
        "Model file not found. Check MODEL_PATH or data_training/model_v3.joblib."
    ) from e

# Ensure shared log file exists with correct header
os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        writer.writeheader()

app = FastAPI(
    title="Sohail Applicant Screening API",
    description="v4 — Production-hardened API with security, validation, and performance monitoring.",
    version="4.0.0"
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


# ── Security: input size limit middleware ────────────────────────────────
@app.middleware("http")
async def size_limit_middleware(request: Request, call_next):
    """Reject requests with body size exceeding MAX_REQUEST_SIZE_MB."""
    content_length = request.headers.get("content-length")
    if content_length:
        size_mb = int(content_length) / (1024 * 1024)
        if size_mb > MAX_REQUEST_SIZE_MB:
            logger.warning(
                f"Request rejected: body size {size_mb:.2f} MB exceeds {MAX_REQUEST_SIZE_MB} MB limit"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request too large",
                    "detail": f"Request body exceeds {MAX_REQUEST_SIZE_MB} MB limit."
                }
            )
    return await call_next(request)


# ── Global error handlers (safe — never leak internals) ──────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a clean 422. Never expose stack traces or internal paths."""
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
    """Catch-all: generic message to client, full details logged server-side only."""
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "Something went wrong while processing the request. Please try again later."
        }
    )


# ── Core prediction logic ────────────────────────────────────────────────
def engineer_features(gpa: float, skills_count: int, prior_projects: int) -> dict:
    """Compute the two engineered features expected by Khaled's v3 Pipeline."""
    return {
        "experience_score": skills_count + prior_projects,
        "high_gpa": 1 if gpa >= 3.5 else 0
    }


def run_prediction(gpa, skills_count, prior_projects, track):
    """Run prediction through Khaled's frozen v3 Pipeline."""
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
    """Append one prediction row to the shared predictions_log.csv."""
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
        logger.error(f"Could not write to prediction log at {LOG_FILE}: {e}")


# ── Endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    with timed_operation("health_check"):
        return {
            "status": "ok",
            "message": "Sohail Applicant Screening API v4 is running.",
            "version": "4.0.0"
        }


@app.post("/predict", response_model=PredictionOutput, responses={422: {"model": ErrorResponse}})
def predict(applicant: ApplicantInput):
    """Single applicant prediction with Khaled's validate_input integration."""
    with timed_operation("predict_single"):
        # Convert Pydantic model to dict for Khaled's validator
        record = applicant.model_dump()

        # Step 1: Khaled's validation (unified across model + API)
        is_valid, result = validate_input(record)
        if not is_valid:
            logger.warning(f"Validation rejected single prediction: {result}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"error": "Invalid input", "detail": result}
            )

        cleaned = result  # cleaned record with proper types

        # Step 2: Predict
        try:
            label, confidence, eng = run_prediction(
                cleaned["gpa"], cleaned["skills_count"],
                cleaned["prior_projects"], cleaned["track"]
            )
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Prediction failed",
                    "detail": "The model could not score this applicant."
                }
            )

        # Step 3: Log
        log_prediction(
            cleaned["gpa"], cleaned["skills_count"], cleaned["prior_projects"],
            cleaned["track"], eng, label, confidence
        )

    return PredictionOutput(prediction=label, confidence=confidence)


@app.post("/predict-batch", responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}})
async def predict_batch(file: UploadFile = File(...)):
    """
    Batch prediction from a CSV file.
    Security: max file size 2 MB, max 500 rows.
    """
    with timed_operation("predict_batch"):
        # ── File type check ───────────────────────────────────────────────
        if not file.filename.lower().endswith(".csv"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid file type", "detail": "Please upload a .csv file."}
            )

        # ── File size check ───────────────────────────────────────────────
        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_BATCH_FILE_SIZE_MB:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "File too large",
                    "detail": f"Batch file exceeds {MAX_BATCH_FILE_SIZE_MB} MB limit."
                }
            )

        if not contents:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Empty file", "detail": "The uploaded CSV file has no content."}
            )

        # ── Parse CSV ─────────────────────────────────────────────────────
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Unreadable CSV",
                    "detail": "The file could not be parsed as a valid CSV."
                }
            )

        required_cols = {"gpa", "skills_count", "prior_projects", "track"}
        missing = required_cols - set(df.columns)
        if missing:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Missing columns",
                    "detail": f"CSV is missing required columns: {sorted(missing)}"
                }
            )

        if len(df) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "No rows", "detail": "The CSV file has headers but no data rows."}
            )

        # ── Row count limit ───────────────────────────────────────────────
        if len(df) > MAX_BATCH_ROWS:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Too many rows",
                    "detail": f"Batch CSV exceeds {MAX_BATCH_ROWS} rows. Please split into smaller files."
                }
            )

        # ── Process rows ──────────────────────────────────────────────────
        results = []
        errors = []

        for idx, row in df.iterrows():
            record = {
                "gpa": row.get("gpa"),
                "skills_count": row.get("skills_count"),
                "prior_projects": row.get("prior_projects"),
                "track": row.get("track")
            }

            # Use Khaled's validator for each row
            is_valid, result = validate_input(record)
            if not is_valid:
                errors.append({"row": int(idx), "error": result})
                continue

            cleaned = result
            try:
                label, confidence, eng = run_prediction(
                    cleaned["gpa"], cleaned["skills_count"],
                    cleaned["prior_projects"], cleaned["track"]
                )
                log_prediction(
                    cleaned["gpa"], cleaned["skills_count"], cleaned["prior_projects"],
                    cleaned["track"], eng, label, confidence
                )
                results.append({
                    "row": int(idx),
                    "gpa": cleaned["gpa"],
                    "skills_count": cleaned["skills_count"],
                    "prior_projects": cleaned["prior_projects"],
                    "track": cleaned["track"],
                    "experience_score": eng["experience_score"],
                    "high_gpa": eng["high_gpa"],
                    "prediction": label,
                    "confidence": confidence
                })
            except Exception as e:
                logger.error(f"Batch row {idx} prediction failed: {e}")
                errors.append({"row": int(idx), "error": "Prediction engine error"})

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
    """Clean HTML dashboard showing latest predictions with improved UX."""
    with timed_operation("results_dashboard"):
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

        # Track breakdown
        track_counts = {}
        for r in rows:
            t = r.get("track", "Unknown")
            track_counts[t] = track_counts.get(t, 0) + 1

        track_bars = ""
        for track, count in sorted(track_counts.items()):
            pct = round(count / total * 100, 1) if total > 0 else 0
            track_bars += (
                '<div style="margin-bottom:8px;">'
                '<div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:3px;">'
                f'<span>{track}</span><span>{count} ({pct}%)</span></div>'
                '<div style="background:#e2e8f0;border-radius:6px;height:10px;overflow:hidden;">'
                f'<div style="background:#3b82f6;width:{pct}%;height:100%;border-radius:6px;"></div></div></div>'
            )

        rows_html = ""
        for r in reversed(rows):
            badge_color = "#22c55e" if r.get("prediction") == "Shortlisted" else "#f59e0b"
            conf_pct = round(r.get("confidence", 0) * 100, 1)
            rows_html += (
                "<tr>"
                f"<td>{r.get('timestamp', '')}</td>"
                f"<td>{r.get('gpa', '')}</td>"
                f"<td>{r.get('skills_count', '')}</td>"
                f"<td>{r.get('prior_projects', '')}</td>"
                f"<td><span class='track-tag'>{r.get('track', '')}</span></td>"
                f"<td>{r.get('experience_score', '')}</td>"
                f"<td>{r.get('high_gpa', '')}</td>"
                f"<td><span class='badge' style='background:{badge_color}'>{r.get('prediction', '')}</span></td>"
                f"<td><div class='conf-bar'><div style='width:{conf_pct}%'></div></div></td>"
                "</tr>"
            )

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sohail Applicant Screening — Results Dashboard</title>
<style>
  :root {{ --primary: #1e3a5f; --success: #16a34a; --warning: #d97706; --blue: #2563eb; --slate: #475569; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.5; }}
  header {{ background: var(--primary); color: white; padding: 28px 32px; }}
  header h1 {{ font-size: 1.6rem; font-weight: 600; }}
  header p {{ font-size: 0.9rem; opacity: 0.8; margin-top: 4px; }}
  .container {{ padding: 24px 32px; max-width: 1400px; margin: 0 auto; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: white; border-radius: 12px; padding: 22px 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }}
  .card .label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }}
  .card .value {{ font-size: 2.2rem; font-weight: 700; margin-top: 6px; }}
  .card.green .value {{ color: var(--success); }}
  .card.amber .value {{ color: var(--warning); }}
  .card.blue .value {{ color: var(--blue); }}
  .card.slate .value {{ color: var(--slate); }}
  .two-col {{ display: grid; grid-template-columns: 1fr 320px; gap: 24px; }}
  @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  .panel {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }}
  .panel h2 {{ font-size: 1rem; color: #475569; margin-bottom: 16px; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: var(--primary); color: white; padding: 12px 14px; text-align: left; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }}
  td {{ padding: 11px 14px; font-size: 0.87rem; border-bottom: 1px solid #f1f5f9; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f8fafc; }}
  .badge {{ color: #fff; padding: 3px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; display: inline-block; }}
  .track-tag {{ background: #e0e7ff; color: #3730a3; padding: 2px 10px; border-radius: 8px; font-size: 0.78rem; font-weight: 600; }}
  .conf-bar {{ background: #e2e8f0; border-radius: 6px; height: 8px; width: 80px; overflow: hidden; }}
  .conf-bar div {{ background: #3b82f6; height: 100%; border-radius: 6px; }}
  .empty-state {{ text-align: center; color: #94a3b8; padding: 48px 24px; }}
  footer {{ text-align: center; padding: 24px; color: #94a3b8; font-size: 0.8rem; }}
</style>
</head>
<body>
<header>
  <h1>&#128203; Sohail Applicant Screening — Results Dashboard</h1>
  <p>v4 Production API &nbsp;|&nbsp; Showing latest {min(total, 50)} predictions &nbsp;|&nbsp; {now_utc}</p>
</header>
<div class="container">
  <div class="stats">
    <div class="card slate"><div class="label">Total Predictions</div><div class="value">{total}</div></div>
    <div class="card green"><div class="label">Shortlisted</div><div class="value">{shortlisted}</div></div>
    <div class="card amber"><div class="label">Review Later</div><div class="value">{review_later}</div></div>
    <div class="card blue"><div class="label">Avg Confidence</div><div class="value">{avg_conf}</div></div>
  </div>
  <div class="two-col">
    <div class="panel">
      <h2>&#128202; Prediction Log</h2>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Time</th><th>GPA</th><th>Skills</th><th>Projects</th>
              <th>Track</th><th>Exp</th><th>High GPA</th><th>Result</th><th>Conf</th>
            </tr>
          </thead>
          <tbody>
            {rows_html if rows_html else '<tr><td colspan="9"><div style="padding:32px;color:#94a3b8;text-align:center;">No predictions yet. Use /predict or /predict-batch to get started.</div></td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
    <div class="panel">
      <h2>&#128200; Track Breakdown</h2>
      {track_bars if track_bars else '<p style="color:#94a3b8;font-size:0.9rem;">No data yet.</p>'}
      <h2 style="margin-top:24px;">&#8505;&#65039; About</h2>
      <p style="font-size:0.85rem;color:#64748b;line-height:1.6;">
        This dashboard shows predictions from the Sohail Applicant Screening ML Service.
        <br><br>
        <strong>Shortlisted</strong> = High-potential applicants recommended for interview.
        <br>
        <strong>Review Later</strong> = Applicants needing further evaluation.
        <br><br>
        For help, see the <a href="/docs" style="color:#2563eb;">API Docs</a>.
      </p>
    </div>
  </div>
</div>
<footer>&copy; Sohail Applicant Screening ML Service — v4.0.0</footer>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/performance")
def get_performance():
    """Return recorded performance metrics (for internal review)."""
    single_times = [m["response_time_ms"] for m in performance_log if m["operation"] == "predict_single"]
    batch_times = [m["response_time_ms"] for m in performance_log if m["operation"] == "predict_batch"]
    return {
        "measurements": performance_log,
        "count": len(performance_log),
        "summary": {
            "avg_predict_single_ms": round(sum(single_times) / max(1, len(single_times)), 2),
            "avg_predict_batch_ms": round(sum(batch_times) / max(1, len(batch_times)), 2),
            "total_single_calls": len(single_times),
            "total_batch_calls": len(batch_times)
        }
    }
