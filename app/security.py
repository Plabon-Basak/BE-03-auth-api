
from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Enter your Supabase access token.",
    auto_error=False,
)