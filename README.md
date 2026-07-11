# sohail-applicant-screening-ml-service-v3
Production-ready ML applicant screening service built with FastAPI, including model packaging, deployment, automated monitoring, alerts, testing, and documentation for internship handover.

## Repo structure

```
repo/
  data_training/   Khaled — frozen model_v3.joblib, training script, MODEL_CARD.md
  api/             Easa — deployed FastAPI service, tests, Dockerfile, API_README.md
  monitoring/      Omar — scheduled monitoring script, alert rules, MONITORING_GUIDE.md
  Dockerfile       Builds and runs the api/ layer with the frozen model + shared log
```

## Quickstart (clone-and-run)

```bash
docker build -t applicant-screening-api .
docker run -p 8000:8000 -v $(pwd)/monitoring:/app/monitoring applicant-screening-api
curl http://localhost:8000/health
```

Then open `http://localhost:8000/results` for the dashboard or `http://localhost:8000/docs` for interactive API docs. Full details in [`api/API_README.md`](api/API_README.md), [`data_training/MODEL_CARD.md`](data_training/MODEL_CARD.md), and [`monitoring/MONITORING_GUIDE.md`](monitoring/MONITORING_GUIDE.md).

**Known handover item:** `data_training/requirements.txt` and `api/requirements.txt` currently pin different scikit-learn versions (`1.7.0` vs `1.6.1`) because the frozen model was pickled under `1.6.1`. See the coordination notes at the bottom of `api/API_README.md`.


