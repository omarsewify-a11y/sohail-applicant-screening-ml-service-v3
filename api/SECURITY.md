# API Security Documentation — v4

Owner: Easa Nazir (API Hardening, Security & User Experience)
Date: 2026-07-22

---

## Security Overview

The v4 API implements defense-in-depth security measures to protect against common API vulnerabilities. This document explains what protections are in place, why they matter, and how they were implemented.

---

## 1. Input Validation & Size Limits

### What Is Protected Against
- **Oversized requests** that could exhaust server memory
- **Malformed input** that could crash the model or leak data
- **Batch abuse** where an attacker uploads massive CSV files

### Implementation

| Layer | Protection | Code Location |
|-------|-----------|---------------|
| Request body size | Max 5 MB per request | `size_limit_middleware` in `main_v4.py` |
| Batch file size | Max 2 MB per upload | `predict_batch()` file size check |
| Batch row count | Max 500 rows per CSV | `predict_batch()` row count check |
| Field validation | Type, range, required checks | Khaled's `validate_input()` + Pydantic |

### Error Response (Safe)
```json
{
  "error": "Request too large",
  "detail": "Request body exceeds 5 MB limit."
}
```

**Why this is safe:** The error tells the user what went wrong without revealing internal limits, file paths, or system architecture.

---

## 2. Safe Error Responses (No Information Leakage)

### What Is Protected Against
- **Information disclosure** — attackers learning about your system from error messages
- **Stack trace exposure** — revealing code structure and vulnerabilities
- **Path disclosure** — showing where files are stored on the server

### Implementation

| Error Type | v3 Behavior | v4 Behavior |
|-----------|-------------|-------------|
| Validation error | Clean JSON (good) | Clean JSON + Khaled's validator |
| Server crash | Generic message (good) | Generic message + server-side logging |
| Missing model file | RuntimeError with path | RuntimeError logged, generic startup failure |

### Forbidden in Error Responses

The following are **never** included in HTTP responses:

- ❌ File paths (`../data_training/model_v3.joblib`, `/app/monitoring/...`)
- ❌ Model filenames (`model_v3.joblib`)
- ❌ Library names (`joblib`, `scikit-learn`)
- ❌ Internal variable names
- ❌ Python exception types or stack traces
- ❌ Database or log file names
- ❌ Environment variable names (except generic ones like "MODEL_PATH")

### What Users See Instead

```json
{
  "error": "Internal server error",
  "detail": "Something went wrong while processing the request. Please try again later."
}
```

### What Gets Logged (Server-Side Only)

```
2026-07-22 14:30:15 [ERROR] Unhandled error on /predict: FileNotFoundError: model_v3.joblib not found at /app/data_training/
```

**Key principle:** Users get helpful but generic messages. Administrators get detailed logs.

---

## 3. Secret Management

### What Is Protected Against
- **Hardcoded secrets** in source code
- **Secret exposure** in error messages or logs
- **Environment variable leakage** through debug endpoints

### Implementation

| Secret Type | How It's Protected |
|-------------|-------------------|
| Model path | `MODEL_PATH` env var, never exposed in responses |
| Log file path | `LOG_PATH` env var, never exposed in responses |
| API keys (if added later) | Would use env vars + `os.getenv()`, never hardcoded |

### Code Pattern

```python
# GOOD: Secret in env var, never exposed
MODEL_PATH = os.getenv("MODEL_PATH", "../data_training/model_v3.joblib")

# BAD: Secret hardcoded or exposed
# return {"model_path": MODEL_PATH}  # NEVER DO THIS
```

---

## 4. Unified Validation (Khaled's `validate_input`)

### What Is Protected Against
- **Inconsistent validation** between API and model pipeline
- **Invalid data reaching the model** and causing crashes or nonsense predictions
- **Type confusion** (e.g., JSON floats vs. Python ints)

### Implementation

The API calls Khaled's `validate_input()` **before** every prediction:

```python
# Single prediction
is_valid, result = validate_input(record)
if not is_valid:
    return JSONResponse(status_code=422, content={"error": "Invalid input", "detail": result})

# Batch prediction — same validator per row
for idx, row in df.iterrows():
    is_valid, result = validate_input(record)
    if not is_valid:
        errors.append({"row": int(idx), "error": result})
        continue
```

**Benefits:**
- One source of truth for validation rules
- Model and API stay in sync automatically
- Edge cases tested by Khaled are automatically enforced by the API

---

## 5. Logging Security

### What Is Protected Against
- **Sensitive data in logs** (though this API doesn't handle PII)
- **Log injection** — attackers manipulating log format
- **Log file exposure** through the API

### Implementation

| Practice | Implementation |
|----------|---------------|
| No PII in logs | Only GPA, skills, projects, track are logged — no names or emails |
| Structured logging | CSV format with fixed columns, easy to parse |
| Log failure isolation | If logging fails, the API continues (doesn't crash) |
| Log file not served | `/results` reads and renders logs, never serves raw file |

---

## 6. Known Limitations & Future Hardening

| Limitation | Risk Level | Recommended Fix (v5) |
|-----------|-----------|---------------------|
| No authentication | Medium | Add API key or OAuth2 for production |
| No rate limiting | Medium | Add per-IP rate limit (e.g., 100 req/min) |
| No HTTPS enforcement | Low | Render provides HTTPS; add HSTS header |
| No input sanitization for XSS | Low | Current inputs are numeric/enum; add escaping if text fields added |
| CSV injection risk | Low | Current data is numeric; sanitize if free-text added |
| No request signing | Low | Not needed at current scale |
| Single worker | Low | Use gunicorn + multiple workers for production load |

---

## 7. Security Test Checklist

Use this checklist during the Friday checkpoint:

- [ ] Submit GPA = 99 → get 422, no file paths in error
- [ ] Submit track = "Hacking" → get 422, no internal details
- [ ] Upload 10 MB file → get 413, clean message
- [ ] Upload 501-row CSV → get 413, clean message
- [ ] Check `/performance` → no secrets exposed
- [ ] Check `/health` → no version details that aid reconnaissance
- [ ] Trigger 500 error → generic message, details in server logs only
- [ ] Inspect all error responses → confirm no `model_v3`, `joblib`, paths, or traces

---

## 8. Coordination with Teammates

| Teammate | Security Coordination Item |
|----------|---------------------------|
| Khaled | `validate_input()` is the single validation gate — any schema changes must be synced |
| Omar | Log format is fixed — adding new columns requires updating both API and monitoring |
| DevOps | `MODEL_PATH` and `LOG_PATH` env vars must be set correctly in production; never commit `.env` files |

---

*This document is part of the v4 security hardening deliverable. Review and update before each release.*
