import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# Load dataset
df = pd.read_csv("applicants_v3.csv")

# ----------------------------
# Feature Engineering
# ----------------------------

df["experience_score"] = (
    df["skills_count"] +
    df["prior_projects"]
)

df["high_gpa"] = (
    df["gpa"] >= 3.5
).astype(int)

# ----------------------------
# Features & Target
# ----------------------------

X = df[
    [
        "gpa",
        "skills_count",
        "prior_projects",
        "experience_score",
        "high_gpa",
        "track"
    ]
]

y = df["shortlisted"]

# ----------------------------
# Preprocessing
# ----------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "track",
            OneHotEncoder(handle_unknown="ignore"),
            ["track"]
        )
    ],
    remainder="passthrough"
)

# ----------------------------
# Pipeline
# ----------------------------

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression())
])

# ----------------------------
# Cross Validation
# ----------------------------

scores = cross_val_score(
    pipeline,
    X,
    y,
    cv=5
)

print("Cross Validation Scores:", scores)
print("Mean Accuracy:", scores.mean())

# ----------------------------
# Train Model
# ----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

pipeline.fit(X_train, y_train)

# ----------------------------
# Save Model
# ----------------------------

joblib.dump(
    pipeline,
    "model_v3.joblib"
)

print("Model Version 3 Saved Successfully!")
