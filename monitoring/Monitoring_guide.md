Monitoring Guide

Purpose

The monitoring system tracks the health of the Applicant Screening ML Service by analyzing prediction logs.

Metrics Tracked

Total predictions
Number of shortlisted applicants
Number of review later applicants
Average prediction confidence
Shortlist rate
Alert Rules

The monitoring script generates alerts when:

Average confidence drops below the defined threshold.
Shortlist rate becomes unusually high.
Shortlist rate becomes unusually low.
Recommended Actions

Low Confidence

Review incoming applicant data and consider retraining the model.

High Shortlist Rate

Inspect whether the input data has changed significantly.

Low Shortlist Rate

Check for possible data quality issues or model performance degradation.
