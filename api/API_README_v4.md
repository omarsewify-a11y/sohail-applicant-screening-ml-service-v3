# API Layer — v4 (Productization & Quality Hardening)

Owner: Easa Nazir

Production-hardened serving layer with security, performance tracking, and improved UX.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /health | Liveness check |
| POST | /predict | Single applicant (with validate_input) |
| POST | /predict-batch | Batch CSV (max 500 rows, 2MB) |
| GET | /results | HTML dashboard |
| GET | /performance | Live performance metrics |

## Security

- Input size limits: 5MB body, 2MB batch file, 500 batch rows
- Safe errors: no stack traces, paths, or secrets leaked
- Unified validation via Khaled's validate_input()

## Running

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
pytest test_api.py -v

