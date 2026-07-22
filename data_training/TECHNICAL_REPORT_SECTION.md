# Data & Model Training Layer

## Overview

Throughout this internship, I was responsible for designing, training, improving, and documenting the machine learning model used in the Sohail Applicant-Screening ML Service. My work focused on creating a reliable and reproducible model capable of predicting whether an internship applicant should be shortlisted or reviewed later.

## Version 1

The first version introduced a basic Logistic Regression model trained on applicant data containing GPA, skills count, prior projects, and track. The objective was to understand the complete machine learning workflow, including data preparation, feature selection, train/test splitting, model training, prediction, and evaluation.

## Version 2

The second version improved the overall workflow by introducing a Scikit-learn Pipeline. This combined preprocessing and model training into a single reusable object, ensuring consistent preprocessing during both training and prediction. Additional validation using cross-validation improved confidence in the model's performance.

## Version 3

Version 3 focused on documentation and reproducibility. A complete Model Card was created describing the model's purpose, dataset, features, limitations, and performance. Requirements were documented to allow teammates to recreate the environment and retrain the model when necessary.

## Version 4

The final production-quality version introduced input validation and edge-case testing. Invalid values, missing fields, and unseen categories were detected before reaching the prediction pipeline. Model quality documentation was expanded to include known limitations and robustness testing.

## Final Model

The final model was packaged as `model_final.joblib` and serves as the official production-ready artifact. Together with the training script, documentation, validation layer, and model card, the model is ready for deployment and long-term maintenance.

## Key Decisions

- Used Logistic Regression for simplicity and interpretability.
- Combined preprocessing and prediction into a Pipeline.
- Used OneHotEncoder for categorical features.
- Applied cross-validation for more reliable evaluation.
- Added reusable validation functions for production robustness.
- Documented every component to support future maintenance.

## Outcome

The final solution provides a reproducible and maintainable machine learning model that integrates with the API and monitoring layers while following software engineering best practices.
