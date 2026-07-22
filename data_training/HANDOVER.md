# Applicant-Screening ML Service – Handover

## Model Package

The final machine learning model has been saved as:

```
model_final.joblib
```

The model is trained using the official applicant dataset and should not be retrained by the API or monitoring components.

## Required Input

The model expects the following applicant information:

- GPA
- Skills Count
- Prior Projects
- Track

The preprocessing pipeline is included within the saved model.

## Validation

All incoming records should be validated before prediction using the reusable validation function.

Validation checks include:

- Required fields
- Numeric data types
- GPA range (0–4)
- Non-negative skills and project counts
- Valid track names

## Integration

The API should load the model directly using Joblib.

The monitoring layer should only receive validated prediction results.

## Documentation

Additional documentation is available in:

- MODEL_CARD.md
- MODEL_QUALITY.md
- DATA_SCHEMA.md
- README.md

## Final Notes

The project is packaged for reproducibility and future maintenance. Any future improvements should focus on expanding the dataset, introducing additional applicant features, and periodically retraining the model using updated data.
