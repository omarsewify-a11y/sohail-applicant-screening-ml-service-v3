def validate_input(record):
    """
    Validate a single applicant record before prediction.
    Returns (True, "Valid") if everything is correct,
    otherwise (False, error_message).
    """

    required_fields = [
        "gpa",
        "skills_count",
        "prior_projects",
        "track"
    ]

    # Check required fields
    for field in required_fields:
        if field not in record:
            return False, f"Missing field: {field}"

    # GPA
    if not isinstance(record["gpa"], (int, float)):
        return False, "GPA must be numeric"

    if record["gpa"] < 0 or record["gpa"] > 4:
        return False, "GPA must be between 0 and 4"

    # Skills
    if not isinstance(record["skills_count"], int):
        return False, "skills_count must be an integer"

    if record["skills_count"] < 0:
        return False, "skills_count cannot be negative"

    # Projects
    if not isinstance(record["prior_projects"], int):
        return False, "prior_projects must be an integer"

    if record["prior_projects"] < 0:
        return False, "prior_projects cannot be negative"

    # Track
    allowed_tracks = ["AI", "Data", "Web"]

    if record["track"] not in allowed_tracks:
        return False, "Unknown track"

    return True, "Valid"
