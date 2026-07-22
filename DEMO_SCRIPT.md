# Sohail Applicant-Screening ML Service — End-to-End Demo Script

**Version:** 4.0  
**Date:** 2026-07-24  
**Team:** Khaled Khaled (Model), Omar Sewify (Monitoring), Easa Nazir (API)

---

## Demo Setup

### Prerequisites
- API running locally or on Render
- Terminal with `curl` installed
- Browser for dashboard viewing

### Start the API (if running locally)
```bash
cd api
export MODEL_PATH=../data_training/model_final.joblib
export LOG_PATH=../monitoring/predictions_log.csv
uvicorn main:app --reload
```

**Base URL:**
- Local: `https://sohail-applicant-screening-api.onrender.com`
- Render: `https://your-service.onrender.com`

---

## Demo Part 1: Health Check (Prove the Service is Live)

**Command:**
```bash
curl https://sohail-applicant-screening-api.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "Sohail Applicant Screening API v4 is running.",
  "version": "4.0.0"
}
```

**What to say:** "The API is live and running version 4.0. This confirms the deployment is healthy."

---

## Demo Part 2: Single Applicant Prediction

**Command:**
```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict   -H "Content-Type: application/json"   -d '{
    "gpa": 3.8,
    "skills_count": 8,
    "prior_projects": 5,
    "track": "AI"
  }'
```

**Expected Response:**
```json
{
  "prediction": "Shortlisted",
  "confidence": 0.822
}
```

**What to say:** "This is a strong applicant — high GPA, many skills and projects, in the AI track. The model is 82% confident they should be shortlisted."

---

## Demo Part 3: Low-Scoring Applicant (Show Model Range)

**Command:**
```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict   -H "Content-Type: application/json"   -d '{
    "gpa": 2.1,
    "skills_count": 1,
    "prior_projects": 0,
    "track": "Web"
  }'
```

**Expected Response:**
```json
{
  "prediction": "Review Later",
  "confidence": 0.9997
}
```

**What to say:** "This applicant has low GPA, minimal skills, and no projects. The model is 99.97% confident they need further review before any decision."

---

## Demo Part 4: Invalid Input (Show Validation)

**Command:**
```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict   -H "Content-Type: application/json"   -d '{
    "gpa": 5.0,
    "skills_count": 5,
    "prior_projects": 2,
    "track": "AI"
  }'
```

**Expected Response:**
```json
{
  "error": "Invalid input",
  "detail": "GPA must be between 0.0 and 4.0"
}
```

**What to say:** "The API rejects invalid input before it reaches the model. This protects the system from bad data and prevents crashes. Notice the error is clean and helpful — no technical details leaked."

---

## Demo Part 5: Batch Prediction (Show Scale)

**Create a sample CSV file:**
```bash
cat > demo_batch.csv << 'EOF'
gpa,skills_count,prior_projects,track
3.8,8,5,AI
2.1,1,0,Web
3.6,6,4,Data
2.9,3,2,AI
3.9,10,7,Data
EOF
```

**Command:**
```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict-batch   -F "file=@demo_batch.csv"
```

**Expected Response:**
```json
{
  "total_rows": 5,
  "successful": 5,
  "failed": 0,
  "shortlisted": 3,
  "review_later": 2,
  "results": [...],
  "errors": []
}
```

**What to say:** "For bulk processing, recruiters can upload a CSV. The API scores all valid rows and reports any failures. Here, 3 out of 5 were shortlisted."

---

## Demo Part 6: Batch with Bad Rows (Show Robustness)

**Create a CSV with invalid rows:**
```bash
cat > demo_batch_bad.csv << 'EOF'
gpa,skills_count,prior_projects,track
3.8,8,5,AI
9.9,2,1,Web
3.0,4,2,Robotics
3.5,5,2,Data
EOF
```

**Command:**
```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict-batch   -F "file=@demo_batch_bad.csv"
```

**Expected Response:**
```json
{
  "total_rows": 4,
  "successful": 2,
  "failed": 2,
  "shortlisted": 1,
  "review_later": 1,
  "results": [...],
  "errors": [
    {"row": 1, "error": "GPA must be between 0.0 and 4.0"},
    {"row": 2, "error": "track must be one of: AI, Data, Web"}
  ]
}
```

**What to say:** "Even with bad data, the API doesn't crash. Good rows are scored, bad rows are reported with clear error messages. This is critical for real-world use where data quality varies."

---

## Demo Part 7: Results Dashboard (Show UX)

**Open in browser:**
```bash
open https://sohail-applicant-screening-api.onrender.com/results
```

**What to show:**
- Total predictions counter
- Shortlisted vs Review Later split
- Average confidence score
- Track breakdown chart
- Prediction log table with color-coded badges

**What to say:** "This dashboard gives non-technical users a clear view of all predictions. Recruiters can see trends without writing code."

---

## Demo Part 8: Performance Metrics (Show Observability)

**Command:**
```bash
curl https://sohail-applicant-screening-api.onrender.com/performance
```

**Expected Response:**
```json
{
  "measurements": [...],
  "count": 42,
  "summary": {
    "avg_predict_single_ms": 18.5,
    "avg_predict_batch_ms": 245.3,
    "total_single_calls": 35,
    "total_batch_calls": 7
  }
}
```

**What to say:** "The API tracks its own performance. Single predictions average 18ms — fast enough for real-time use. Batch operations scale linearly."

---

## Demo Part 9: Monitoring Integration (Omar's Layer)

**Run monitoring script:**
```bash
cd monitoring
python monitoring.py
```

**View reports:**
```bash
cat monitoring_report.txt
cat alert_log.txt
```

**What to say:** "Every prediction is logged to a shared CSV. Omar's monitoring script reads this and generates business reports and alerts. This closes the loop — from input to insight."

---

## Demo Part 10: Security Verification

**Test that errors don't leak secrets:**
```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict   -H "Content-Type: application/json"   -d '{"gpa":99,"skills_count":5,"prior_projects":2,"track":"AI"}'
```

**Verify response does NOT contain:**
- `model_final` or `joblib`
- `data_training` or file paths
- `predictions_log` or log paths
- Stack traces or exception names

**What to say:** "Security is built in. Even when things go wrong, attackers learn nothing about our system internals."

---

## Demo Summary

| Step | What We Showed |
|------|---------------|
| 1 | Service is live and healthy |
| 2 | Single prediction works |
| 3 | Model handles both strong and weak applicants |
| 4 | Invalid input is rejected safely |
| 5 | Batch processing scales |
| 6 | Bad rows don't crash the system |
| 7 | Dashboard is user-friendly |
| 8 | Performance is measured |
| 9 | Monitoring closes the loop |
| 10 | Security is verified |

**Closing statement:** "This is the Sohail Applicant-Screening ML Service — built over 8 weeks, deployed, hardened, and ready for production use."

---

## Quick Reference Card

```
HEALTH:     curl https://sohail-applicant-screening-api.onrender.com/health
PREDICT:    curl -X POST https://sohail-applicant-screening-api.onrender.com/predict -H "Content-Type: application/json" -d '{"gpa":3.8,"skills_count":8,"prior_projects":5,"track":"AI"}'
BATCH:      curl -X POST https://sohail-applicant-screening-api.onrender.com/predict-batch -F "file=@batch.csv"
DASHBOARD:  https://sohail-applicant-screening-api.onrender.com/results
PERFORMANCE: curl https://sohail-applicant-screening-api.onrender.com/performance
DOCS:       https://sohail-applicant-screening-api.onrender.com/docs
```
