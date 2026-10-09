
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.security import bearer_scheme
from app.supabase_client import supabase


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Access token required",
        )

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        user = response.user
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return user