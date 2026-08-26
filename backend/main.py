from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Market Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "service": "Market Intelligence",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "connected": False,
        "message": "Backend is working"
    }

@app.get("/debug")
def debug():
    return {
        "status": "debug works",
        "file": "backend/main.py",
        "version": "2026-08-27-v2"
    }

@app.get("/scanner")
def scanner():
    return {
        "status": "ready",
        "message": "Scanner endpoint is working",
        "stocks": []
    }


@app.get("/config")
def config():
    return {
        "configured": False,
        "symbols": []
    }
