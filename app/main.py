
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from gotrue.errors import AuthApiError

from app.auth import get_current_user
from app.schemas import AuthRequest
from app.security import bearer_scheme
from app.supabase_client import supabase
import httpx

from app.supabase_client import SUPABASE_URL, SUPABASE_KEY

app = FastAPI(
    title="FlyRank BE-03 Auth API",
    description="Authentication API using FastAPI and Supabase Auth.",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    missing_fields = {
        error["loc"][-1]
        for error in exc.errors()
        if error.get("type") == "missing" and error.get("loc")
    }

    if "email" in missing_fields or "password" in missing_fields:
        message = "Email and password are required"
    else:
        message = "Invalid request body"

    return JSONResponse(
        status_code=400,
        content={"error": message},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
        headers=exc.headers,
    )


@app.get("/")
async def root():
    return {
        "message": "FlyRank BE-03 Auth API is running",
        "supabase_initialized": supabase is not None,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/signup", status_code=201)
async def signup(data: AuthRequest):
    try:
        response = supabase.auth.sign_up(
            {
                "email": str(data.email),
                "password": data.password,
            }
        )
    except AuthApiError:
        raise HTTPException(
            status_code=400,
            detail="Unable to create account. Check your details and try again.",
        )

    if response.user is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to create account",
        )

    return {
        "user": response.user.model_dump(mode="json"),
    }


@app.post("/auth/login", status_code=200)
async def login(data: AuthRequest):
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": str(data.email),
                "password": data.password,
            }
        )
    except AuthApiError:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials",
        )

    if response.user is None or response.session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials",
        )

    return {
        "user": response.user.model_dump(mode="json"),
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
        "token_type": "bearer",
    }


@app.get("/public/info")
async def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


@app.get("/protected/profile")
async def protected_profile(
    user=Depends(get_current_user),
):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


@app.get("/protected/dashboard")
async def protected_dashboard(
    user=Depends(get_current_user),
):
    return {
        "message": f"Welcome to your dashboard, {user.email}",
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }



@app.post("/auth/logout", status_code=204)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    user=Depends(get_current_user),
):
    token = credentials.credentials

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SUPABASE_URL.rstrip('/')}/auth/v1/logout",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {token}",
                },
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact authentication service",
        )

    if response.status_code in (200, 204):
        return Response(status_code=204)

    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    raise HTTPException(
        status_code=502,
        detail="Authentication service logout failed",
    )