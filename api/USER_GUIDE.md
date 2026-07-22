# Sohail Applicant Screening Service — User Guide

**For: HR Managers, Recruiters, and Hiring Coordinators**

**Version:** 4.0 (Production-Ready)

---

## What Is This Service?

The **Sohail Applicant Screening Service** is a smart tool that helps you quickly decide which internship applicants are strong candidates and which ones need a closer look.

It uses a machine learning model trained on past applicant data to give each candidate a score:

| Result | What It Means | Recommended Action |
|--------|--------------|-------------------|
| **Shortlisted** | Strong candidate | Schedule an interview |
| **Review Later** | Needs more evaluation | Review resume manually or conduct a phone screen |

---

## How to Access the Service

### Option 1: Dashboard (Easiest)

Open your web browser and go to:

```
https://your-api-url/results
```

(Replace `your-api-url` with the live URL your IT team gave you.)

You will see:
- **Total predictions** made today
- How many were **Shortlisted** vs **Review Later**
- **Average confidence** of the model
- A breakdown by track (AI, Data, Web)
- A table of the latest 50 predictions

![Dashboard Preview](dashboard-preview.png)

*The dashboard updates automatically every time someone submits a new applicant.*

---

### Option 2: Score One Applicant at a Time

Use this when you want to check one applicant quickly.

**What you need:**
- The applicant's **GPA** (0.0 to 4.0)
- **Number of technical skills** they have (e.g., Python, SQL, React)
- **Number of past projects** they've completed
- Their **internship track**: AI, Data, or Web

**How to do it:**

1. Go to the interactive API docs:
   ```
   https://your-api-url/docs
   ```

2. Click on **`POST /predict`**

3. Click **"Try it out"**

4. Fill in the form:
   ```json
   {
     "gpa": 3.7,
     "skills_count": 6,
     "prior_projects": 3,
     "track": "AI"
   }
   ```

5. Click **"Execute"**

6. You will see the result:
   ```json
   {
     "prediction": "Shortlisted",
     "confidence": 0.85
   }
   ```

   - **prediction**: Shortlisted or Review Later
   - **confidence**: How sure the model is (0.0 = not sure, 1.0 = very sure)

---

### Option 3: Score Many Applicants at Once (Batch Upload)

Use this when you have a spreadsheet of many applicants.

**Step 1: Prepare your CSV file**

Create a file named `applicants.csv` with these exact column headers:

```csv
gpa,skills_count,prior_projects,track
```

Then add one row per applicant:

```csv
gpa,skills_count,prior_projects,track
3.8,8,5,AI
2.1,1,0,Web
3.6,6,4,Data
3.9,10,7,Data
2.5,3,1,AI
```

**Rules for the CSV:**
- ✅ GPA must be between **0.0 and 4.0**
- ✅ `skills_count` and `prior_projects` must be **0 or higher**
- ✅ `track` must be exactly **AI**, **Data**, or **Web** (case-sensitive)
- ✅ Maximum **500 rows** per file
- ✅ Maximum file size **2 MB**
- ❌ No missing values allowed

**Step 2: Upload the file**

1. Go to:
   ```
   https://your-api-url/docs
   ```

2. Click on **`POST /predict-batch`**

3. Click **"Try it out"**

4. Under `file`, click **"Choose File"** and select your `applicants.csv`

5. Click **"Execute"**

6. You will see a summary:
   ```json
   {
     "total_rows": 5,
     "successful": 5,
     "failed": 0,
     "shortlisted": 3,
     "review_later": 2,
     "results": [ ... ],
     "errors": []
   }
   ```

   - **successful**: How many applicants were scored
   - **failed**: How many had bad data and were skipped
   - **results**: Full details for each applicant
   - **errors**: Which rows had problems (if any)

**If some rows fail:**
- The good rows are still scored
- Bad rows are listed in `errors` with a reason (e.g., "GPA must be between 0 and 4")
- Fix the bad rows and re-upload just those

---

## Understanding the Results

### Confidence Score

The confidence score tells you how sure the model is:

| Confidence | Interpretation |
|-----------|----------------|
| **0.90 – 1.00** | Very confident — trust this result |
| **0.70 – 0.89** | Fairly confident — good to use |
| **0.50 – 0.69** | Uncertain — consider manual review |
| **Below 0.50** | Low confidence — definitely review manually |

**Important:** The model is a helper, not a replacement for human judgment. Always review borderline cases manually.

---

## Common Issues & How to Fix Them

| Problem | Cause | Solution |
|---------|-------|----------|
| "Invalid input" error | GPA is above 4.0 or below 0.0 | Check the GPA value and fix it |
| "Unknown track" error | Track is not AI, Data, or Web | Use exact spelling: AI, Data, or Web |
| "Missing field" error | A required column is empty | Fill in all required fields |
| "File too large" error | CSV is bigger than 2 MB | Split into smaller files (max 500 rows each) |
| "Too many rows" error | More than 500 applicants in one file | Split the file and upload in parts |
| Dashboard shows old data | Browser cache | Press **Ctrl+F5** (Windows) or **Cmd+Shift+R** (Mac) to refresh |

---

## Security & Privacy

- **No personal data stored:** The service only stores GPA, skills count, projects, track, and the prediction result. It does **not** store names, emails, or resumes.
- **Safe errors:** If something goes wrong, you get a clean, helpful message — never technical details that could expose the system.
- **Access control:** The API is protected by your organization's network. Do not share the URL publicly.

---

## Tips for Best Results

1. **Be consistent with data entry** — use the same rules for counting skills and projects across all applicants
2. **Update the model regularly** — as you hire more interns, the model should be retrained with new data (ask your data team)
3. **Flag edge cases** — if the model gives surprising results, note them and share with the data team for improvement
4. **Use batch upload for efficiency** — scoring 50 applicants one-by-one takes time; batch upload does it in seconds

---

## Need Help?

| Issue | Contact |
|-------|---------|
| The website won't load | IT Support |
| You got a confusing prediction result | Data Science Team (Khaled) |
| You want to change alert thresholds | Monitoring Team (Omar) |
| The API is slow or unresponsive | API Team (Easa) |
| You want to add new features or fields | Product Manager |

---

## Quick Reference Card

```
SINGLE APPLICANT:
  URL: /predict
  Needs: GPA (0.0-4.0), Skills (#), Projects (#), Track (AI/Data/Web)
  Returns: Shortlisted or Review Later + Confidence

BATCH APPLICANTS:
  URL: /predict-batch
  Needs: CSV file with columns: gpa, skills_count, prior_projects, track
  Limits: Max 500 rows, Max 2 MB
  Returns: Summary + detailed results + any errors

DASHBOARD:
  URL: /results
  Shows: Latest predictions, stats, track breakdown
```

---

*This guide is part of the Sohail Applicant Screening ML Service v4 documentation.*
*Last updated: 2026-07-22*
