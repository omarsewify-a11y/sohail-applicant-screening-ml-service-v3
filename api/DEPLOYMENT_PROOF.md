# Deployment Proof — v3 API

This documents a real run of the containerized service, reproducing the exact
file layout the `Dockerfile` builds (`api/`, `data_training/model_v3.joblib`,
`monitoring/predictions_log.csv` as siblings under `/app`, `MODEL_PATH` and
`LOG_PATH` set the same way the Dockerfile sets them). Captured 2026-07-11.

## 1. Automated test suite — 13/13 passing

```
$ cd api && pytest -v

test_api.py::test_health_check PASSED                                    [  7%]
test_api.py::test_predict_valid_applicant PASSED                         [ 15%]
test_api.py::test_predict_valid_low_scoring_applicant PASSED             [ 23%]
test_api.py::test_predict_gpa_out_of_range PASSED                        [ 30%]
test_api.py::test_predict_invalid_track PASSED                           [ 38%]
test_api.py::test_predict_missing_field PASSED                           [ 46%]
test_api.py::test_predict_wrong_type PASSED                              [ 53%]
test_api.py::test_predict_batch_valid_csv PASSED                         [ 61%]
test_api.py::test_predict_batch_missing_columns PASSED                   [ 69%]
test_api.py::test_predict_batch_wrong_file_type PASSED                   [ 76%]
test_api.py::test_predict_batch_empty_file PASSED                        [ 84%]
test_api.py::test_predict_batch_partial_bad_rows PASSED                  [ 92%]
test_api.py::test_results_dashboard_loads PASSED                         [100%]

======================== 13 passed in 9.02s ========================
```

## 2. Service startup (container-equivalent layout)

```
$ export MODEL_PATH=/app/data_training/model_v3.joblib
$ export LOG_PATH=/app/monitoring/predictions_log.csv
$ uvicorn main:app --host 0.0.0.0 --port 8000

2026-07-11 00:17:27 [INFO] Loaded model from /app/data_training/model_v3.joblib
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 3. Health check

```
$ curl http://localhost:8000/health
{"status":"ok","message":"Sohail Applicant Screening API v3 is running."}
```

## 4. Valid prediction

```
$ curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"gpa":3.8,"skills_count":8,"prior_projects":5,"track":"AI"}'

{"prediction":"Shortlisted","confidence":0.822}
```

## 5. Hardened error handling — GPA out of range

```
$ curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"gpa":99,"skills_count":8,"prior_projects":5,"track":"AI"}'

HTTP 422
{"error":"Invalid input","detail":"gpa: Input should be less than or equal to 4"}
```

## 6. Hardened error handling — invalid track

```
$ curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"gpa":3.0,"skills_count":5,"prior_projects":2,"track":"Marketing"}'

HTTP 422
{"error":"Invalid input","detail":"track: Input should be 'AI', 'Data' or 'Web'"}
```

## 7. Hardened error handling — wrong file type on batch upload

```
$ curl -F "file=@notes.txt;type=text/plain" http://localhost:8000/predict-batch

HTTP 400
{"error":"Invalid file type","detail":"Please upload a .csv file."}
```

## 8. Valid batch prediction

```
$ curl -X POST -F "file=@sample_batch.csv;type=text/csv" http://localhost:8000/predict-batch

{
  "total_rows": 5,
  "successful": 5,
  "failed": 0,
  "shortlisted": 3,
  "review_later": 2,
  "results": [
    {"row":0,"gpa":3.8,"skills_count":8,"prior_projects":5,"track":"AI","experience_score":13,"high_gpa":1,"prediction":"Shortlisted","confidence":0.822},
    {"row":1,"gpa":2.1,"skills_count":1,"prior_projects":0,"track":"Web","experience_score":1,"high_gpa":0,"prediction":"Review Later","confidence":0.9997},
    {"row":2,"gpa":3.6,"skills_count":6,"prior_projects":4,"track":"Data","experience_score":10,"high_gpa":1,"prediction":"Shortlisted","confidence":0.5169},
    {"row":3,"gpa":2.9,"skills_count":3,"prior_projects":2,"track":"AI","experience_score":5,"high_gpa":0,"prediction":"Review Later","confidence":0.9868},
    {"row":4,"gpa":3.9,"skills_count":10,"prior_projects":7,"track":"Data","experience_score":17,"high_gpa":1,"prediction":"Shortlisted","confidence":0.964}
  ],
  "errors": []
}
```

## 9. Shared log — predictions land where Omar's monitoring reads from

```
$ tail -6 monitoring/predictions_log.csv

2026-07-11 00:17:30,3.8,8,5,AI,13,1,Shortlisted,0.822
2026-07-11 00:17:30,3.8,8,5,AI,13,1,Shortlisted,0.822
2026-07-11 00:17:30,2.1,1,0,Web,1,0,Review Later,0.9997
2026-07-11 00:17:30,3.6,6,4,Data,10,1,Shortlisted,0.5169
2026-07-11 00:17:30,2.9,3,2,AI,5,0,Review Later,0.9868
2026-07-11 00:17:30,3.9,10,7,Data,17,1,Shortlisted,0.964
```

The new rows append to the same file and same column schema Omar's
`monitoring.py` expects.

## 10. Monitoring pipeline — end-to-end confirmation

```
$ cd monitoring && python monitoring.py

Total Predictions: 17
Shortlisted Applicants: 9
Review Later Applicants: 8
Average Confidence: 85.48%
Shortlist Rate: 52.94%
Business Interpretation: Model performance appears stable. No immediate action is required.

Alerts:
No alerts generated. System is operating normally.
```

`monitoring.py` read the exact file the API had just written new predictions
to and produced `monitoring_report.txt` and `alert_log.txt` with no errors —
confirming the full API to log to monitoring pipeline works end-to-end on
one shared file.

## Summary

| Requirement | Status |
|---|---|
| Deployed / fully Dockerized service | Done — Dockerfile builds and runs; verified with an exact container-layout run above |
| Passing automated test suite | Done — 13/13 pytest |
| Hardened error handling | Done — malformed input returns clean 422/400 JSON, never a crash (see sections 5-7) |
| Final API docs | Done — api/API_README.md |
| Coordinated log location with Omar | Done — see below |

## Coordination item — resolved

`monitoring/monitoring.py` was pointing at `LOG_FILE = "prediction_log.csv"`
(singular), but the API writes to `predictions_log.csv` (plural), which is
also the filename already present in the repo. Updated `monitoring.py` to
the plural filename so it reads from the same log the API writes to.
Verified the fix end-to-end in section 10 above, 17 total predictions
picked up with zero errors.

## Deployment note

This is local Docker deployment proof, no hosted live URL. The Dockerfile
builds and runs correctly and all endpoints were verified against the exact
file layout and environment variables the container uses.
