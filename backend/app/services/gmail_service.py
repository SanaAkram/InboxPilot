"""
Gmail integration: OAuth flow, token refresh, email sync, and message parsing.
"""
import base64
import email as email_lib
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        return response.json()


def _get_credentials(access_token: str, refresh_token: str, token_expiry: datetime | None) -> Credentials:
    # google-auth's _helpers.utcnow() returns a naive datetime, so expiry must also be naive
    if token_expiry is not None and token_expiry.tzinfo is not None:
        token_expiry = token_expiry.replace(tzinfo=None)
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URL,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
        expiry=token_expiry,
    )


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime_type.startswith("multipart/"):
        for part in payload.get("parts", []):
            text = _extract_body(part)
            if text:
                return text
    return ""


def _parse_message(msg: dict) -> dict[str, Any]:
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    sender_raw = headers.get("from", "")
    # Parse "Name <email>" format
    match = re.match(r"^(.*?)\s*<(.+?)>$", sender_raw)
    if match:
        sender_name = match.group(1).strip().strip('"')
        sender_email = match.group(2).strip()
    else:
        sender_name = ""
        sender_email = sender_raw.strip()

    date_str = headers.get("date", "")
    try:
        received_at = email_lib.utils.parsedate_to_datetime(date_str)
    except Exception:
        received_at = datetime.now(timezone.utc)

    body = _extract_body(msg.get("payload", {}))

    return {
        "gmail_message_id": msg["id"],
        "thread_id": msg.get("threadId"),
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": headers.get("subject", "(no subject)"),
        "body": body,
        "snippet": msg.get("snippet", ""),
        "received_at": received_at,
    }


async def sync_emails(
    access_token: str,
    refresh_token: str,
    token_expiry: datetime | None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """Fetch latest emails from Gmail and return parsed message dicts."""
    creds = _get_credentials(access_token, refresh_token, token_expiry)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("gmail", "v1", credentials=creds)
    result = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages_meta = result.get("messages", [])

    parsed = []
    for meta in messages_meta:
        msg = service.users().messages().get(userId="me", id=meta["id"], format="full").execute()
        parsed.append(_parse_message(msg))
    return parsed


async def get_email(
    gmail_message_id: str,
    access_token: str,
    refresh_token: str,
    token_expiry: datetime | None,
) -> dict[str, Any]:
    creds = _get_credentials(access_token, refresh_token, token_expiry)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    service = build("gmail", "v1", credentials=creds)
    msg = service.users().messages().get(userId="me", id=gmail_message_id, format="full").execute()
    return _parse_message(msg)
