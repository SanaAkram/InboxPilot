import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import create_access_token, get_current_user
from app.models.email_account import EmailAccount
from app.models.user import User
from app.schemas.user import UserOut
from app.services import gmail_service
from app.config import settings

router = APIRouter()


@router.post("/google/login")
async def google_login():
    """Returns the Google OAuth authorization URL."""
    state = secrets.token_urlsafe(16)
    url = gmail_service.build_auth_url(state)
    return {"auth_url": url}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):

    tokens = await gmail_service.exchange_code_for_tokens(code)
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", 3600)
    token_expiry = datetime.now(timezone.utc).replace(microsecond=0)

    user_info = await gmail_service.get_user_info(access_token)
    google_id = user_info["id"]
    email = user_info["email"]
    full_name = user_info.get("name")

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user is None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, full_name=full_name, google_id=google_id)
        db.add(user)
        await db.flush()

    # Upsert email account credentials
    result = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == user.id, EmailAccount.provider == "gmail")
    )
    account = result.scalar_one_or_none()
    if account is None:
        account = EmailAccount(user_id=user.id, provider="gmail")
        db.add(account)

    account.access_token = access_token
    if refresh_token:
        account.refresh_token = refresh_token
    account.token_expiry = token_expiry

    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token(user.id)
    # Redirect to frontend with token
    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={jwt_token}",
        status_code=302,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless; client should discard the token
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
