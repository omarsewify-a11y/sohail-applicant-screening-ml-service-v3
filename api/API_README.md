# API Layer — v3 (Deployment, Testing & Reliability)

Owner: Easa Nazir

This is the deployed serving layer for the Sohail Applicant Screening ML Service. It loads Khaled's frozen `model_v3.joblib`, serves predictions over HTTP, and logs every prediction to the shared file Omar's monitoring layer reads from.

## What changed from v2

- Deployable via Docker (or run locally), not just on a personal machine
- Automated pytest suite covering good and bad input on every endpoint
- Hardened error handling — malformed requests get a clean JSON error, never a raw crash or stack trace
- Model and log paths are configurable via environment variables so the same code runs locally and in a container

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/predict` | Score a single applicant |
| POST | `/predict-batch` | Score a CSV of applicants |
| GET | `/results` | HTML dashboard of the latest 50 predictions |

### `POST /predict`

Request:
```json
{
  "gpa": 3.8,
  "skills_count": 8,
  "prior_projects": 5,
  "track": "AI"
}
```
`track` must be one of `AI`, `Data`, `Web`. `gpa` must be between 0.0 and 4.0.

Response (200):
```json
{
  "prediction": "Shortlisted",
  "confidence": 0.822
}
```

Bad input (422):
```json
{
  "error": "Invalid input",
  "detail": "gpa: Input should be less than or equal to 4"
}
```

### `POST /predict-batch`

Upload a `.csv` file (multipart/form-data, field name `file`) with columns `gpa,skills_count,prior_projects,track`.

Response (200):
```json
{
  "total_rows": 3,
  "successful": 3,
  "failed": 0,
  "shortlisted": 2,
  "review_later": 1,
  "results": [ ... ],
  "errors": [ ... ]
}
```
Rows with bad values (out-of-range GPA, unknown track, etc.) are skipped and reported in `errors` instead of failing the whole batch. Missing columns, an empty file, or a non-CSV file return a `400` with a clear message.

### `GET /results`

Renders an HTML dashboard summarizing the shared prediction log (total predictions, shortlist/review split, average confidence, and the latest 50 rows).

## Running locally

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```
Open `http://localhost:8000/docs` for interactive Swagger docs, or `http://localhost:8000/results` for the dashboard.

By default the API expects to sit inside the repo at `api/`, next to `data_training/` and `monitoring/`:
```
repo/
  api/
  data_training/
  monitoring/
```
It loads the model from `../data_training/model_v3.joblib` and writes predictions to `../monitoring/predictions_log.csv`. Both are overridable with `MODEL_PATH` and `LOG_PATH` environment variables.

## Running with Docker

From the repo root (where the `Dockerfile` lives):

```bash
docker build -t applicant-screening-api .
docker run -p 8000:8000 -v $(pwd)/monitoring:/app/monitoring applicant-screening-api
```

The `-v` volume mount keeps `predictions_log.csv` persisted on the host and in sync with Omar's monitoring script, even as the container is stopped and restarted.

Verify it's running:
```bash
curl http://localhost:8000/health
```

## Running the tests

```bash
cd api
pytest -v
```
13 tests, covering `/health`, valid and invalid `/predict` requests (out-of-range GPA, invalid track, missing field, wrong type), valid and invalid `/predict-batch` requests (missing columns, wrong file type, empty file, partially bad rows), and `/results`. Tests write to an isolated `test_predictions_log.csv`, never the shared log.

## Error handling summary

| Situation | Response |
|---|---|
| Missing/invalid field in `/predict` | `422` with `error` + `detail` |
| GPA out of 0.0–4.0 range | `422` |
| Track not in `AI`/`Data`/`Web` | `422` |
| Non-CSV file to `/predict-batch` | `400` |
| Empty CSV | `400` |
| CSV missing required columns | `400` |
| A few bad rows in an otherwise valid CSV | `200`, bad rows reported in `errors`, good rows still scored |
| Unexpected server error | `500` with a generic message (details are logged server-side, not leaked to the client) |

## Coordination notes for handover

- **Model contract (Khaled):** the API sends `gpa, skills_count, prior_projects, experience_score, high_gpa, track` to `model_v3.joblib`, matching `data_training/train_model_v3.py` exactly. `experience_score` and `high_gpa` are computed the same way on both sides (see `engineer_features()` in `main.py`).
- **Dependency pin mismatch found during deployment testing:** `data_training/requirements.txt` pins `scikit-learn==1.7.0`, but `model_v3.joblib` was actually pickled under `scikit-learn==1.6.1` — loading it under 1.7.0 raises an `AttributeError` (`_RemainderColsList`) and the API won't start. This API's `requirements.txt` pins `1.6.1` to match the real artifact and load successfully. **Action needed:** Khaled should either re-pin `data_training/requirements.txt` to `1.6.1`, or retrain and re-freeze the model under `1.7.0` — whichever the team wants as the source of truth — so both requirements files agree.
- **Shared log location (Omar):** this API writes to `monitoring/predictions_log.csv` with columns `timestamp, gpa, skills_count, prior_projects, track, experience_score, high_gpa, prediction, confidence`, matching the file already in the repo. **Action needed:** `monitoring/monitoring.py` currently points at `prediction_log.csv` (singular, no "s") — that filename doesn't exist. Omar should update it to `predictions_log.csv` so the monitoring script reads what the API actually writes.
- **Deployment proof:** see the Docker run output and `curl /health` / `/predict` results below (or the live URL, if hosted) for evidence the service runs outside a personal machine.
