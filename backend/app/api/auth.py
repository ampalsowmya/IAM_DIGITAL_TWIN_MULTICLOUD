from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from .deps import User, create_access_token


router = APIRouter(tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@router.post(
    "/auth/token",
    response_model=TokenResponse,
    summary="Obtain JWT access token",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """
    Issue a JWT token for demo users.

    This implementation uses a fixed set of in-memory demo users:
    - admin / admin (role=admin)
    - analyst / analyst (role=analyst)
    - viewer / viewer (role=viewer)

    Example response:
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "role": "admin"
    }
    """

    demo_users = {
        "admin": "admin",
        "analyst": "analyst",
        "viewer": "viewer",
    }
    roles = {
        "admin": "admin",
        "analyst": "analyst",
        "viewer": "viewer",
    }
    username = form_data.username
    password = form_data.password
    if username not in demo_users or demo_users[username] != password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    role = roles[username]
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": username, "role": role},
        expires_delta=access_token_expires,
    )
    return TokenResponse(access_token=access_token, role=role)

