from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router


load_dotenv()

app = FastAPI(title="MP1 -- Murder Mystery Party Generator")
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_DIR = BASE_DIR.parent / "client"

app.mount("/static", StaticFiles(directory=CLIENT_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(CLIENT_DIR / "index.html")
