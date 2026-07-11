# Pushing v3 to GitHub

Run these from inside the extracted `sohail-applicant-screening-ml-service-v3-main` folder,
after you've merged in Khaled's and Omar's latest files if they've pushed updates.

```bash
# If this isn't already a git repo pointing at the shared repo:
git init
git remote add origin https://github.com/omarsewify-a11y/sohail-applicant-screening-ml-service-v2-2.git
# same shared repo as v2 — just a new branch, per the task brief

git checkout -b v3
git add .
git commit -m "v3: deployed FastAPI service, Dockerfile, pytest suite, hardened error handling, API docs"
git push -u origin v3
```

Repo link to submit:
`https://github.com/omarsewify-a11y/sohail-applicant-screening-ml-service-v2-2/tree/v3`

## If Omar pushes his monitoring.py fix after you push

```bash
git pull origin v3
```
to pick up his change before final submission — no need to touch your own files.
