# Model Quality Report

## Cross Validation

The Applicant Screening Model was evaluated using 5-fold cross-validation.

The average accuracy remained consistent across all folds, indicating stable model performance and low variance.

---

## Classification Performance

The model performs well when predicting whether an applicant should be shortlisted or reviewed later.

Performance was evaluated using:

- Accuracy
- Cross-validation
- Per-class prediction consistency

---

## Edge Case Testing

Several invalid input scenarios were tested.

| Test Case | Result |
|-----------|--------|
| GPA above 4.0 | Rejected |
| Negative skills count | Rejected |
| Unknown track | Rejected |
| Missing required field | Rejected |

---

## Limitations

The model still has several limitations:

- Uses synthetic training data.
- Limited number of applicant features.
- Cannot replace human hiring decisions.
- Performance may decrease with completely unseen applicant profiles.

---

## Conclusion

The validation layer significantly improves model reliability by preventing invalid data from reaching the prediction pipeline.
