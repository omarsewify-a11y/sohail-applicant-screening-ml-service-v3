# Integration Documentation

## Overview

This document explains how Version 3 integrates with the remaining system components.

---

## Model File

The trained model is provided as:

```
model_v3.joblib
```

The API loads this model directly.

No retraining is performed inside the API.

---

## Input Schema

Required fields:

- gpa
- skills_count
- prior_projects
- track

The pipeline automatically generates the required preprocessing internally.

---

## Prediction Output

The API returns:

```json
{
  "prediction": "shortlist",
  "confidence": 0.97
}
```

---

## Monitoring

Every prediction is stored inside:

```
predictions_log.csv
```

This file is used by the Monitoring Layer.

---

## Dependencies

All required package versions are defined in:

```
requirements.txt
```

---

## Reproducibility

Training always uses

```
random_state = 42
```

ensuring consistent results across team members.

---

## Team Integration

Data Training Layer

↓

Model Version 3

↓

API Layer

↓

Prediction Log

↓

Monitoring Layer

This workflow ensures consistency across the complete Applicant Screening Service.
