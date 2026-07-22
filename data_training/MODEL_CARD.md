# Model Card

## Model Name

Applicant Screening Model

## Purpose

Predict whether an internship applicant should be shortlisted or reviewed later.

## Model Type

Logistic Regression

## Dataset

Synthetic applicant dataset including:

- GPA
- Skills Count
- Prior Projects
- Track

## Features

| Feature | Type |
|----------|------|
| GPA | Numeric |
| Skills Count | Numeric |
| Prior Projects | Numeric |
| Track | Categorical |

## Target

Shortlisted

- 1 = Shortlist
- 0 = Review Later

## Training

The model was trained using a Scikit-learn Pipeline with preprocessing and Logistic Regression.

Cross-validation was performed using five folds.

## Performance

The model achieved consistent performance across cross-validation with stable accuracy.

## Limitations

- Uses synthetic data.
- Limited feature set.
- Cannot replace human hiring decisions.
- Performance depends on data quality.

## Intended Use

Educational demonstration of a complete machine learning workflow for applicant screening.

## Maintenance

Future improvements should include:

- More real-world data
- Additional applicant features
- Regular retraining
- Continuous monitoring
