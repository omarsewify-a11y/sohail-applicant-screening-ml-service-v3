# Model Card

## Model Name

Applicant Screening Model Version 3

---

## Purpose

This machine learning model predicts whether an internship applicant should be shortlisted or marked for further review based on several applicant attributes.

---

## Dataset

Synthetic internship applicant dataset.

80 applicant records.

---

## Features

- GPA
- Skills Count
- Prior Projects
- Track
- Experience Score
- High GPA Indicator

---

## Target

shortlisted

- 1 = Shortlisted
- 0 = Review Later

---

## Model

- Logistic Regression
- Scikit-learn Pipeline

---

## Preprocessing

The Pipeline automatically performs:

- One-Hot Encoding for Track
- Numeric feature passthrough

No manual preprocessing is required during prediction.

---

## Validation

5-Fold Cross Validation

Random State:

```python
42
```

---

## Performance

The model achieved a strong average cross-validation accuracy during testing.

---

## Limitations

- Uses synthetic internship data.
- Small dataset.
- Should not be used for real hiring decisions.
- Additional real-world applicant features would improve performance.

---

## Version

Version 3 (Final Handover Version)
