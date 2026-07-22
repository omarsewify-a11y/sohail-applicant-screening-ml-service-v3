# Friday Quality Checkpoint — v4

**Date:** 2026-07-25 (Friday)
**Team:** Sohail Applicant Screening ML Service v4
**Branch:** `v4`

| Member | Role | Checkpoint Focus |
|--------|------|-----------------|
| Khaled Khaled | Model Quality, Validation & Data Robustness | `validate_input()` integration, edge cases |
| Omar Sewify | Monitoring Hardening & Business Reporting | Log format, alert firing, business report |
| Easa Nazir | API Hardening, Security & User Experience | API security, performance, UX, docs |

---

## 1. Pre-Checkpoint Setup

Before starting the joint test, confirm:
- [ ] All team members have pulled the latest `v4` branch
- [ ] The API is running locally or on the live URL
- [ ] Khaled's `validate_input()` is in `data_training/validation.py`
- [ ] Omar's monitoring script points to `predictions_log.csv` (plural)
- [ ] The shared log file exists and is writable

**Command to start the API for testing:**
```bash
cd api
pip install -r requirements.txt
uvicorn main_v4:app --reload
```

**Live URL (if deployed):** `https://sohail-applicant-screening-api.onrender.com`

---

## 2. Test Scenarios

### 2.1 Valid Input Test (All Layers)

**Test:** Submit a valid applicant through the API and verify end-to-end flow.

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"gpa":3.8,"skills_count":8,"prior_projects":5,"track":"AI"}'
```

**Expected:**
- [ ] API returns 200 with prediction and confidence
- [ ] Khaled's `validate_input()` accepts the input (no rejection)
- [ ] Prediction is logged to `monitoring/predictions_log.csv`
- [ ] Omar's monitoring script can read the new row
- [ ] Dashboard (`/results`) shows the new prediction

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.2 Bad Input Rejection Test (Khaled + Easa Integration)

**Test:** Submit invalid inputs and confirm they are rejected before reaching the model.

| Bad Input | curl Command | Expected Status | Expected Error |
|-----------|-------------|-----------------|----------------|
| GPA > 4.0 | `{"gpa":5.0,"skills_count":5,"prior_projects":2,"track":"AI"}` | 422 | "GPA must be between 0.0 and 4.0" |
| Negative skills | `{"gpa":3.0,"skills_count":-1,"prior_projects":2,"track":"AI"}` | 422 | "skills_count cannot be negative" |
| Unknown track | `{"gpa":3.0,"skills_count":5,"prior_projects":2,"track":"Marketing"}` | 422 | "track must be one of: AI, Data, Web" |
| Missing field | `{"gpa":3.0,"skills_count":5,"track":"AI"}` | 422 | "Missing field: prior_projects" |
| Wrong type (GPA = string) | `{"gpa":"abc","skills_count":5,"prior_projects":2,"track":"AI"}` | 422 | "GPA must be a number" |

**For each test, confirm:**
- [ ] API returns the correct HTTP status
- [ ] Error message is clean and helpful (no stack traces)
- [ ] Error message does NOT contain: file paths, model names, internal details
- [ ] Model is NEVER called for invalid input
- [ ] Nothing is written to the prediction log for rejected requests

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.3 Batch Upload Security Test

**Test:** Upload various CSV files to test security limits.

| Test Case | File Content | Expected Result |
|-----------|-------------|-----------------|
| Valid CSV | 5 good rows | 200, all scored |
| Missing columns | `gpa,skills_count
3.8,8
` | 400, "Missing columns" |
| Wrong file type | `notes.txt` | 400, "Invalid file type" |
| Empty file | Empty `.csv` | 400, "Empty file" |
| Partial bad rows | 2 good + 2 bad rows | 200, 2 successful, 2 errors listed |
| Too many rows | 501 rows | 413, "Too many rows" |
| Oversized file | >2 MB CSV | 413, "File too large" |

**Confirm:**
- [ ] Good rows are scored and logged
- [ ] Bad rows are reported in `errors` array with clear reasons
- [ ] No server crash on any input

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.4 Performance Test

**Test:** Measure response times under normal load.

```bash
# Single prediction (run 10 times)
for i in {1..10}; do
  curl -w "\n%{time_total}\n" -o /dev/null -s \
    -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"gpa":3.5,"skills_count":5,"prior_projects":2,"track":"Data"}'
done

# Batch prediction (50 rows)
curl -w "\n%{time_total}\n" -o /dev/null -s \
  -F "file=@batch_50.csv" http://localhost:8000/predict-batch
```

**Acceptance Criteria:**
- [ ] Single prediction: < 100 ms average
- [ ] Batch (50 rows): < 1 second
- [ ] Dashboard load: < 100 ms
- [ ] Health check: < 10 ms

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.5 Secret Leakage Test (Security)

**Test:** Verify that error responses never expose internal details.

```bash
# Trigger various errors and inspect responses
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"gpa":99,"skills_count":5,"prior_projects":2,"track":"AI"}'

curl -X POST http://localhost:8000/predict-batch \
  -F "file=@bad.csv"
```

**Check that responses do NOT contain:**
- [ ] `model_v3` or `joblib`
- [ ] `data_training` or file paths like `../` or `/app/`
- [ ] `predictions_log.csv` or log file paths
- [ ] Python stack traces or exception names
- [ ] Internal variable names or function names

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.6 Monitoring Integration Test (Omar + Easa)

**Test:** Confirm Omar's monitoring works with the API's log output.

```bash
# 1. Make a few predictions
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"gpa":3.9,"skills_count":10,"prior_projects":7,"track":"Data"}'

curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"gpa":2.1,"skills_count":1,"prior_projects":0,"track":"Web"}'

# 2. Run Omar's monitoring script
cd monitoring
python monitoring.py

# 3. Check outputs
cat monitoring_report.txt
cat alert_log.txt
```

**Confirm:**
- [ ] Monitoring script reads `predictions_log.csv` successfully
- [ ] Report shows correct total predictions count
- [ ] Shortlist rate is calculated correctly
- [ ] Average confidence is calculated correctly
- [ ] Alerts fire appropriately (if thresholds are crossed)
- [ ] Monitoring script handles empty/malformed logs gracefully (Omar's v4 hardening)

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.7 Dashboard UX Test

**Test:** Verify the results dashboard is clean and usable.

1. Open `http://localhost:8000/results` in a browser
2. Check:
   - [ ] Page loads without errors
   - [ ] Stats cards show correct numbers
   - [ ] Track breakdown chart is visible
   - [ ] Prediction table is readable
   - [ ] Color coding (green = Shortlisted, amber = Review Later) is clear
   - [ ] Page is responsive on mobile (if tested)
   - [ ] v4 branding is visible

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

### 2.8 Documentation Completeness

**Check that all required docs exist and are accurate:**

- [ ] `api/API_README.md` — updated for v4
- [ ] `api/USER_GUIDE.md` — written for non-developers
- [ ] `api/PERFORMANCE.md` — response times documented
- [ ] `data_training/MODEL_QUALITY.md` — Khaled's quality report
- [ ] `data_training/validation.py` — reusable validator
- [ ] `monitoring/BUSINESS_REPORT.md` — Omar's business report
- [ ] `QUALITY_LOG.md` — this file, completed

**Result:** ⬜ PASS / ⬜ FAIL
**Notes:**

---

## 3. Issue Log

Record any bugs, concerns, or coordination items found during testing:

| # | Issue | Severity | Owner | Status |
|---|-------|----------|-------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## 4. Go/No-Go Decision

**Is v4 ready for final handover (Week 8)?**

| Criterion | Status |
|-----------|--------|
| API is secure (no secret leakage, input limits) | ⬜ PASS / ⬜ FAIL |
| API is robust (handles bad input gracefully) | ⬜ PASS / ⬜ FAIL |
| Performance is measured and acceptable | ⬜ PASS / ⬜ FAIL |
| User experience is clean (dashboard + docs) | ⬜ PASS / ⬜ FAIL |
| Model validation is integrated and working | ⬜ PASS / ⬜ FAIL |
| Monitoring reads logs correctly | ⬜ PASS / ⬜ FAIL |
| All documentation is complete | ⬜ PASS / ⬜ FAIL |

**Overall Decision:** ⬜ **GO** — v4 is production-ready for handover
             ⬜ **NO-GO** — issues must be fixed before Week 8

**Decision made by:** _________________
**Date:** _________________

---

## 5. Post-Checkpoint Actions

If GO:
- [ ] Merge `v4` to `main` (or keep as `v4` for handover)
- [ ] Tag the release: `git tag v4.0.0`
- [ ] Update live deployment if needed
- [ ] Prepare Week 8 handover presentation

If NO-GO:
- [ ] List blocking issues above
- [ ] Assign owners and deadlines
- [ ] Re-run checkpoint after fixes

---

*This QUALITY_LOG.md is a living document. Update it as issues are found and resolved.*
