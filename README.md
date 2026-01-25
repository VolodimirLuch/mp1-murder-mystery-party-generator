# MP1 -- Murder Mystery Party Generator

Full-stack mini project that generates a complete murder mystery party package
using Together.ai. The app includes a browser client and FastAPI server.

## Run Locally

```bash
cd mp1_murder_mystery/server
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Create a `.env` file:

```bash
TOGETHER_API_KEY=your_together_api_key_here
TOGETHER_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Then open `http://localhost:8000` in your browser.
