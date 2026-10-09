
from fastapi import FastAPI

from app.supabase_client import supabase

app = FastAPI(
    title="FlyRank BE-03 Auth API",
    description="Authentication API using FastAPI and Supabase Auth.",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    print("Server running and connected to Supabase")


@app.get("/")
def root():
    return {
        "message": "FlyRank BE-03 Auth API is running",
        "supabase_initialized": supabase is not None,
    }


@app.get("/health")
def health():
    return {"status": "ok"}