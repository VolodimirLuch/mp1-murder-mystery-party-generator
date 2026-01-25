# MP1 -- Murder Mystery Party Generator (Server)

FastAPI backend that generates a murder mystery party package using Together.ai.

## Quickstart

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set `TOGETHER_API_KEY`.

Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `GET /api/categories`
- `POST /api/generate`
- `POST /api/validate`
