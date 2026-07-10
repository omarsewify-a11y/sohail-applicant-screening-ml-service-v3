import pandas as pd
from datetime import datetime


# ==============================
# Load Prediction Log
# ==============================

LOG_FILE = "prediction_log.csv"

df = pd.read_csv(LOG_FILE)


# ==============================
# Calculate Monitoring Metrics
# ==============================

total_predictions = len(df)

shortlisted = (df["prediction"] == "Shortlisted").sum()

review_later = (df["prediction"] == "Review Later").sum()

average_confidence = df["confidence"].mean()

shortlist_rate = (shortlisted / total_predictions) * 100


# ==============================
# Business Interpretation
# ==============================

if average_confidence < 0.75:
    interpretation = (
        "Model confidence is low. "
        "The team should review recent applicant data "
        "and evaluate model performance."
    )

elif shortlist_rate > 90:
    interpretation = (
        "Shortlist rate is unusually high. "
        "The team should check incoming applicant data "
        "for possible changes."
    )

elif shortlist_rate < 10:
    interpretation = (
        "Shortlist rate is unusually low. "
        "The team should inspect model behavior "
        "and data quality."
    )

else:
    interpretation = (
        "Model performance appears stable. "
        "No immediate action is required."
    )


# ==============================
# Generate Monitoring Report
# ==============================

report = f"""
=====================================
Applicant Screening Monitoring Report
=====================================

Generated Time:
{datetime.now()}

Total Predictions:
{total_predictions}

Shortlisted Applicants:
{shortlisted}

Review Later Applicants:
{review_later}

Average Confidence:
{average_confidence:.2%}

Shortlist Rate:
{shortlist_rate:.2f}%

Business Interpretation:
{interpretation}

"""


with open("monitoring_report.txt", "w") as file:
    file.write(report)


# ==============================
# Alert System
# ==============================

alerts = []


# Low confidence alert
if average_confidence < 0.75:
    alerts.append(
        "WARNING: Average confidence dropped below 75%. "
        "Action: Review model performance."
    )


# High shortlist rate alert
if shortlist_rate > 90:
    alerts.append(
        "WARNING: Shortlist rate exceeded 90%. "
        "Action: Check incoming applicant data."
    )


# Low shortlist rate alert
if shortlist_rate < 10:
    alerts.append(
        "WARNING: Shortlist rate dropped below 10%. "
        "Action: Check model and data quality."
    )


if len(alerts) == 0:
    alerts.append(
        "No alerts generated. System is operating normally."
    )


with open("alert_log.txt", "w") as file:
    for alert in alerts:
        file.write(alert + "\n")


# ==============================
# Display Results
# ==============================

print(report)

print("Alerts:")
for alert in alerts:
    print(alert)
