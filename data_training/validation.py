"""
Sohail Applicant Screening — Input Validation (v4)
Owner: Khaled Khaled (Model Quality, Validation & Data Robustness)
Enhanced by Easa Nazir for API compatibility (float→int tolerance)

Reusable validation function used by both the model pipeline and the API layer.
Returns (True, "Valid") for clean input, (False, error_message) for bad input.
"""


def validate_input(record):
    """
    Validate a single applicant record before prediction.

    Parameters
    ----------
    record : dict
        Must contain keys: gpa, skills_count, prior_projects, track
        - gpa: float or int, 0.0 to 4.0
        - skills_count: int or whole-number float, >= 0
        - prior_projects: int or whole-number float, >= 0
        - track: str, one of "AI", "Data", "Web"

    Returns
    -------
    tuple(bool, str)
        (True, "Valid")  — input is clean, safe to predict
        (False, message) — input has a problem, message explains why
    """

    required_fields = ["gpa", "skills_count", "prior_projects", "track"]

    # ── Check required fields ─────────────────────────────────────────────
    for field in required_fields:
        if field not in record:
            return False, f"Missing field: {field}"

    # ── GPA validation ────────────────────────────────────────────────────
    if not isinstance(record["gpa"], (int, float)):
        return False, "GPA must be a number"

    gpa = float(record["gpa"])
    if gpa < 0.0 or gpa > 4.0:
        return False, "GPA must be between 0.0 and 4.0"

    # ── Skills count validation ───────────────────────────────────────────
    # API JSON may send whole-number floats (e.g. 8.0); accept them as ints
    skills = record["skills_count"]
    if isinstance(skills, float):
        if not skills.is_integer():
            return False, "skills_count must be a whole number"
        skills = int(skills)
    elif not isinstance(skills, int):
        return False, "skills_count must be a whole number"
    if skills < 0:
        return False, "skills_count cannot be negative"

    # ── Prior projects validation ─────────────────────────────────────────
    projects = record["prior_projects"]
    if isinstance(projects, float):
        if not projects.is_integer():
            return False, "prior_projects must be a whole number"
        projects = int(projects)
    elif not isinstance(projects, int):
        return False, "prior_projects must be a whole number"
    if projects < 0:
        return False, "prior_projects cannot be negative"

    # ── Track validation ──────────────────────────────────────────────────
    allowed_tracks = {"AI", "Data", "Web"}
    track = str(record["track"]).strip()
    if track not in allowed_tracks:
        return False, f"track must be one of: {', '.join(sorted(allowed_tracks))}"

    # ── Return cleaned record (optional, for API convenience) ─────────────
    cleaned = {
        "gpa": round(gpa, 2),
        "skills_count": skills,
        "prior_projects": projects,
        "track": track
    }

    return True, cleaned
