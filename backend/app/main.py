from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, emails, tasks, briefings

app = FastAPI(
    title="InboxPilot API",
    description="AI-powered inbox management — converts emails into actionable tasks.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(emails.router, prefix="/api/emails", tags=["emails"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(briefings.router, prefix="/api/briefings", tags=["briefings"])


@app.get("/health")
async def health():
    return {"status": "ok"}
