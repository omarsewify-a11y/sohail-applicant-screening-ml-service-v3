import os
import pandas as pd
from datetime import datetime


# =====================================
# Load Prediction Log
# =====================================

LOG_FILE = "predictions_log.csv"


# Check if file exists
if not os.path.exists(LOG_FILE):
    print("ERROR: Prediction log file not found.")
    exit()


# Read CSV safely
try:
    df = pd.read_csv(LOG_FILE)

except Exception as e:
    print("ERROR: Unable to read prediction log.")
    print(e)
    exit()


# Check if log is empty
if df.empty:
    print("WARNING: Prediction log is empty.")
    exit()


# Check required columns
required_columns = [
    "prediction",
    "confidence"
]


for column in required_columns:

    if column not in df.columns:
        print(
            f"ERROR: Missing required column: {column}"
        )
        exit()



# =====================================
# Calculate Monitoring Metrics
# =====================================

total_predictions = len(df)


shortlisted = (
    df["prediction"] == "Shortlisted"
).sum()


review_later = (
    df["prediction"] == "Review Later"
).sum()


average_confidence = (
    df["confidence"].mean()
)


shortlist_rate = (
    shortlisted / total_predictions
) * 100



# =====================================
# Business Interpretation
# =====================================

if average_confidence < 0.70:

    interpretation = (
        "Model confidence is critically low. "
        "Immediate investigation is recommended."
    )


elif average_confidence < 0.85:

    interpretation = (
        "Model confidence is slightly below the desired level. "
        "Continue monitoring and review recent prediction data."
    )


else:

    interpretation = (
        "Model confidence is healthy and predictions appear stable."
    )



# =====================================
# Generate Monitoring Report
# =====================================

report = f"""

==========================================
Applicant Screening Monitoring Report
==========================================

Generated Time:
{datetime.now()}


------------------------------------------
Prediction Statistics
------------------------------------------

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



------------------------------------------
Business Interpretation
------------------------------------------

{interpretation}



------------------------------------------
Recommended Actions
------------------------------------------

• Review monitoring reports regularly.
• Investigate repeated WARNING or CRITICAL alerts.
• Check prediction data quality.
• Retrain the model if confidence decreases continuously.

"""


with open(
    "monitoring_report.txt",
    "w"
) as file:

    file.write(report)



# =====================================
# Alert System
# =====================================

alerts = []


# Confidence alerts

if average_confidence >= 0.85:

    alerts.append(
        "INFO: Model confidence is healthy."
    )


elif average_confidence >= 0.70:

    alerts.append(
        "WARNING: Model confidence is below the desired level."
    )


else:

    alerts.append(
        "CRITICAL: Model confidence is very low. Immediate review required."
    )



# Shortlist rate alerts

if shortlist_rate > 90:

    alerts.append(
        "WARNING: More than 90% of applicants are being shortlisted. Check model behaviour."
    )


elif shortlist_rate < 10:

    alerts.append(
        "WARNING: Shortlist rate dropped below 10%. Check model and data quality."
    )


else:

    alerts.append(
        "INFO: Shortlist rate is within the expected range."
    )



# =====================================
# Save Alert Log
# =====================================

with open(
    "alert_log.txt",
    "w"
) as file:

    file.write(
        "Applicant Screening Alert Log\n"
    )

    file.write(
        f"Generated: {datetime.now()}\n\n"
    )


    for alert in alerts:

        file.write(
            alert + "\n"
        )



# =====================================
# Display Results
# =====================================

print(report)


print(
    "==================================="
)

print(
    "Alerts"
)

print(
    "==================================="
)


for alert in alerts:

    print(alert)



print(
    "\nMonitoring completed successfully."
)
