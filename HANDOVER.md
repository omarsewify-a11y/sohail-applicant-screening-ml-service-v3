# Applicant Screening ML Service — Final Handover

**Prepared for:** Sohail  
**Date:** July 2026  
**Version:** 1.0 (Final)  
**Team:** Khaled (Model), Omar (Monitoring), Easa (API & Deployment)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Overview](#system-overview)
3. [Repository Structure](#repository-structure)
4. [Khaled — Model Layer](#khaled--model-layer)
5. [Easa — API & Deployment Layer](#easa--api--deployment-layer)
6. [Omar — Monitoring & Evaluation Layer](#omar--monitoring--evaluation-layer)
7. [Live Service](#live-service)
8. [How to Run from Fresh Clone](#how-to-run-from-fresh-clone)
9. [End-to-End Demo](#end-to-end-demo)
10. [Maintenance Guide](#maintenance-guide)
11. [Team Contacts](#team-contacts)

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/omarsewify-a11y/sohail-applicant-screening-ml-service-v3.git
cd sohail-applicant-screening-ml-service-v3

# Run locally
cd api
pip install -r requirements.txt
uvicorn main:app --reload

# Or run with Docker
docker build -t screening-api .
docker run -p 8000:8000 screening-api
```

**Live URL:** https://sohail-applicant-screening-api.onrender.com

---

## System Overview

This is a production-ready applicant screening ML service built over 8 weeks.

**What it does:** Predicts whether a job applicant should be "Shortlisted" or "Review Later" based on GPA, skills, projects, and track.

**Architecture (3 layers):**

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: API & Deployment (Easa)                           │
│  FastAPI service, security hardening, performance tracking  │
│  Endpoints: /health, /predict, /predict-batch, /results     │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: Monitoring & Evaluation (Omar)                    │
│  Prediction logging, automated reports, alert system        │
│  Tracks: confidence, shortlist rate, data quality           │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: Model & Data (Khaled)                             │
│  Trained model, validation pipeline, feature engineering    │
│  Model: Random Forest, frozen as model_final.joblib         │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
sohail-applicant-screening-ml-service-v3/
├── api/
│   ├── main.py                 ← FastAPI application (Easa)
│   ├── test_api.py             ← Test suite (Easa)
│   ├── requirements.txt        ← Python dependencies
│   ├── PERFORMANCE.md          ← Performance analysis (Easa)
│   ├── SECURITY.md             ← Security documentation (Easa)
│   ├── USER_GUIDE.md           ← Non-developer guide (Easa)
│   └── API_README_v4.md        ← API documentation (Easa)
│
├── data_training/
│   ├── model_final.joblib      ← Frozen production model (Khaled)
│   ├── model_v3.joblib         ← Previous model version (Khaled)
│   ├── train_model_v3.py       ← Training script (Khaled)
│   ├── validation.py           ← Input validation (Khaled)
│   ├── applicants_v3.csv       ← Training data (Khaled)
│   ├── MODEL_CARD.md           ← Model documentation (Khaled)
│   ├── MODEL_QUALITY.md        ← Quality evidence (Khaled)
│   └── TECHNICAL_REPORT_SECTION.md  ← Khaled's report section
│
├── monitoring/
│   ├── monitoring.py           ← Monitoring script (Omar)
│   ├── predictions_log.csv     ← Prediction history (Omar)
│   ├── BUSINESS_REPORT.md      ← Business summary (Omar)
│   ├── MONITORING_GUIDE.md     ← Usage guide (Omar)
│   ├── QUALITY_LOG.md          ← Quality test results (Omar)
│   ├── monitoring_report.txt   ← Generated report (Omar)
│   ├── alert_log.txt           ← Generated alerts (Omar)
│   ├── README.md               ← Monitoring module docs (Omar)
│   └── TECHNICAL_REPORT_OMAR.md   ← Omar's report section
│
├── Dockerfile                  ← Container config
├── README.md                   ← Main project README
├── HANDOVER.md                 ← This file
├── TECHNICAL_REPORT_SECTION_EASA.md  ← Easa's report section
└── DEMO_SCRIPT.md              ← Demo walkthrough
```

---

## Khaled — Model Layer

**Owner:** Khaled  
**Role:** Data & Model Engineering

### What Was Built

| Version | What Changed |
|---------|-------------|
| v1 | Simple model with basic features |
| v2 | Pipeline + feature engineering (experience_score, high_gpa) |
| v3 | Validation pipeline, honest evaluation, frozen model |
| v4 | Final packaging, model_final.joblib, complete documentation |

### Key Files

- `data_training/model_final.joblib` — Production model (frozen)
- `data_training/train_model_v3.py` — Training script
- `data_training/validation.py` — Input validation (integrated into API)
- `data_training/MODEL_CARD.md` — Full model documentation
- `data_training/MODEL_QUALITY.md` — Evaluation results

### Model Performance

- **Accuracy:** ~85% on validation set
- **Features:** GPA, skills_count, prior_projects, track, experience_score, high_gpa
- **Algorithm:** Random Forest Classifier
- **Validation:** Train/test split with honest evaluation

### How to Retrain

```bash
cd data_training
python train_model_v3.py
```

The script saves a new `model_final.joblib`. Update the API's `MODEL_PATH` environment variable if the filename changes.

---

## Easa — API & Deployment Layer

**Owner:** Easa Nazir  
**Role:** API Development & System Deployment

### What Was Built

| Version | What Changed |
|---------|-------------|
| v1 | Single `/predict` endpoint, basic FastAPI |
| v2 | Batch prediction, error handling, logging |
| v3 | Deployment to Render, documentation, test suite |
| v4 | Security hardening, performance tracking, UX improvements |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| POST | `/predict` | Single applicant prediction |
| POST | `/predict-batch` | Batch CSV upload (max 500 rows, 2MB) |
| GET | `/results` | HTML results dashboard |
| GET | `/performance` | Live performance metrics |

### Security Features

- Input size limits: 5MB body, 2MB batch file, 500 batch rows
- Safe error responses: no stack traces, paths, or secrets leaked
- Unified validation via Khaled's `validate_input()`
- JSON parsing with clear error messages

### Performance Tracking

- Response time logging on all endpoints
- `/performance` endpoint shows average latency
- `PERFORMANCE.md` documents timing analysis

### Key Files

- `api/main.py` — FastAPI application
- `api/test_api.py` — 20+ test suite
- `api/PERFORMANCE.md` — Performance documentation
- `api/SECURITY.md` — Security documentation
- `api/USER_GUIDE.md` — Non-developer guide

---

## Omar — Monitoring & Evaluation Layer

**Owner:** Omar Sewify  
**Role:** Quality Assurance & Production Monitoring

### What Was Built

| Version | What Changed |
|---------|-------------|
| v1 | Initial model evaluation (confusion matrix, accuracy) |
| v2 | Production monitoring script, prediction logging |
| v3 | Business reporting, automated alerts |
| v4 | Final quality evidence, complete monitoring system |

### Monitoring System

The monitoring layer tracks system health after deployment:

**Metrics Tracked:**
- Total predictions
- Shortlisted vs Review Later counts
- Average prediction confidence
- Shortlist rate (%)

**Alert Rules:**
- **INFO:** Normal operation
- **WARNING:** Confidence below 85% or shortlist rate outside 10-90%
- **CRITICAL:** Confidence below 70% — immediate investigation required

**Generated Reports:**
- `monitoring/monitoring_report.txt` — Full statistics report
- `monitoring/alert_log.txt` — Alert summary

### How to Run Monitoring

```bash
cd monitoring
python monitoring.py
```

This reads `predictions_log.csv` and generates:
- Console output with statistics
- `monitoring_report.txt` — Detailed report
- `alert_log.txt` — Alert status

### Quality Evidence

The monitoring system has been tested against:
- Normal prediction logs ✅
- Missing prediction logs ✅
- Empty prediction logs ✅
- Malformed prediction logs ✅
- Low confidence values ✅
- Abnormal shortlist rates ✅

See `monitoring/QUALITY_LOG.md` for full test results.

### Key Files

- `monitoring/monitoring.py` — Main monitoring script
- `monitoring/BUSINESS_REPORT.md` — Business summary
- `monitoring/MONITORING_GUIDE.md` — Usage instructions
- `monitoring/QUALITY_LOG.md` — Quality test evidence
- `monitoring/TECHNICAL_REPORT_OMAR.md` — Omar's report section

---

## Live Service

**URL:** https://sohail-applicant-screening-api.onrender.com

### Quick Health Check

```bash
curl https://sohail-applicant-screening-api.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "Sohail Applicant Screening API v4 is running.",
  "version": "4.0.0"
}
```

### Test Prediction

```bash
curl -X POST https://sohail-applicant-screening-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"gpa":3.8,"skills_count":8,"prior_projects":5,"track":"AI"}'
```

### View Dashboard

Open in browser: https://sohail-applicant-screening-api.onrender.com/results

---

## How to Run from Fresh Clone

### Option A: Local (Python)

```bash
# 1. Clone
git clone https://github.com/omarsewify-a11y/sohail-applicant-screening-ml-service-v3.git
cd sohail-applicant-screening-ml-service-v3

# 2. Install dependencies
cd api
pip install -r requirements.txt

# 3. Set environment variables
export MODEL_PATH=../data_training/model_final.joblib
export LOG_PATH=../monitoring/predictions_log.csv

# 4. Start server
uvicorn main:app --reload

# 5. Test
curl http://localhost:8000/health
```

### Option B: Docker

```bash
# 1. Clone
git clone https://github.com/omarsewify-a11y/sohail-applicant-screening-ml-service-v3.git
cd sohail-applicant-screening-ml-service-v3

# 2. Build and run
docker build -t screening-api .
docker run -p 8000:8000 screening-api

# 3. Test
curl http://localhost:8000/health
```

### Option C: Run Monitoring

```bash
cd monitoring
python monitoring.py
```

---

## End-to-End Demo

See `DEMO_SCRIPT.md` for the full 10-step demonstration:

1. Health check
2. Single prediction
3. Batch prediction
4. Results dashboard
5. Performance metrics
6. Monitoring report
7. Alert system
8. Error handling
9. Security verification
10. System summary

**Quick demo command:**
```bash
cd api && pytest test_api.py -v
```

---

## Maintenance Guide

### Daily
- Check `/health` endpoint
- Review `monitoring/alert_log.txt`
- Monitor prediction volume

### Weekly
- Run `monitoring/monitoring.py` and review report
- Check shortlist rate trends
- Review `api/PERFORMANCE.md` for latency changes

### Monthly
- Retrain model if confidence degrades (see Khaled's section)
- Review security logs
- Update dependencies

### When Alerts Fire

| Alert | Action |
|-------|--------|
| WARNING: Low confidence | Review recent data, check for drift |
| WARNING: Abnormal shortlist rate | Inspect input data for changes |
| CRITICAL: Very low confidence | Immediate investigation, consider retraining |

---

## Team Contacts

| Role | Name | Responsibility |
|------|------|---------------|
| Model & Data | Khaled | Model training, validation, retraining |
| API & Deployment | Easa Nazir | API maintenance, deployment, security |
| Monitoring & Evaluation | Omar Sewify | Quality monitoring, alerting, reporting |

---

## Final Notes

This service was built over 8 weeks as a capstone internship project.

**v1:** Prototype model and basic API  
**v2:** Production pipeline and deployment  
**v3:** Documentation, testing, live deployment  
**v4:** Security hardening, performance tracking, UX  
**Week 8:** Final consolidation, handover, and demo

All code is documented, tested, and ready for production use.

**For questions or issues, refer to:**
- `api/USER_GUIDE.md` — How to use the API
- `api/SECURITY.md` — Security details
- `monitoring/MONITORING_GUIDE.md` — Monitoring instructions
- `data_training/MODEL_CARD.md` — Model documentation

---

*End of Handover Document*
