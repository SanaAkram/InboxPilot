"""
AI service: email classification, task extraction, and daily briefing generation.
Provider is auto-detected from environment: ANTHROPIC_API_KEY takes precedence over OPENAI_API_KEY.
"""
import json
from datetime import date
from typing import Any

import anthropic
from openai import AsyncOpenAI

from app.config import settings

_anthropic_client: anthropic.AsyncAnthropic | None = None
_openai_client: AsyncOpenAI | None = None


def _get_provider() -> str:
    if settings.anthropic_api_key:
        return "anthropic"
    if settings.openai_api_key:
        return "openai"
    raise RuntimeError("No AI API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


async def _call_ai(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.1,
    json_mode: bool = False,
    creative: bool = False,
) -> str:
    """
    Unified AI call. `creative=True` enables adaptive thinking (Anthropic) or
    higher temperature (OpenAI) — used for the briefing generator.
    """
    provider = _get_provider()

    if provider == "anthropic":
        kwargs: dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if creative:
            kwargs["thinking"] = {"type": "adaptive"}
        else:
            kwargs["temperature"] = temperature
        response = await _get_anthropic_client().messages.create(**kwargs)
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    else:  # openai
        kwargs = {
            "model": settings.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7 if creative else temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await _get_openai_client().chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""


async def classify_email(subject: str, body: str, sender: str) -> dict:
    """
    Returns:
        {
            "category": str,   # invoice|meeting|support|urgent|followup|sales|personal|other
            "priority": str,   # low|medium|high|critical
            "summary": str,
            "action_required": bool,
            "confidence": float
        }
    """
    prompt = f"""You are an AI email classifier for a productivity tool.

Analyze this email and return ONLY valid JSON with these exact fields:
- category: one of [invoice, meeting, support, urgent, followup, sales, personal, other]
- priority: one of [low, medium, high, critical]
- summary: one sentence summarizing the email
- action_required: boolean, whether the user needs to take action
- confidence: float between 0.0 and 1.0

Email:
From: {sender}
Subject: {subject}
Body:
{body[:2000]}

Respond with JSON only. No markdown, no explanation."""

    text = await _call_ai(prompt, max_tokens=512, temperature=0.1, json_mode=True)
    return json.loads(text or "{}")


async def extract_tasks(subject: str, body: str, sender: str) -> dict:
    """
    Returns:
        {
            "tasks": [
                {
                    "title": str,
                    "action_type": str,  # reply|schedule|review|approve|pay|followup|call|other
                    "priority": str,     # low|medium|high|critical
                    "deadline": str | null  # ISO date YYYY-MM-DD or null
                }
            ]
        }
    """
    today = date.today().isoformat()
    prompt = f"""You are an AI that extracts actionable tasks from emails.

Today's date is {today}.

Analyze this email and return ONLY valid JSON with a "tasks" array. Each task must have:
- title: short action title (verb + object, e.g. "Reply to meeting request")
- action_type: one of [reply, schedule, review, approve, pay, followup, call, other]
- priority: one of [low, medium, high, critical]
- deadline: ISO date string (YYYY-MM-DD) if a date is mentioned, otherwise null

Email:
From: {sender}
Subject: {subject}
Body:
{body[:2000]}

Return {{"tasks": []}} if no action is required.
Respond with JSON only. No markdown, no explanation."""

    text = await _call_ai(prompt, max_tokens=1024, temperature=0.1, json_mode=True)
    return json.loads(text or '{"tasks": []}')


async def generate_briefing(emails_summary: list[dict], pending_tasks: list[dict]) -> str:
    """
    Generates a plain-text daily briefing.

    emails_summary: list of {sender, subject, category, priority}
    pending_tasks:  list of {title, priority, deadline}
    """
    emails_text = "\n".join(
        f"- [{e['priority'].upper()}] {e['subject']} from {e['sender']} ({e['category']})"
        for e in emails_summary[:20]
    )
    tasks_text = "\n".join(
        f"- [{t['priority'].upper()}] {t['title']}" + (f" (due {t['deadline']})" if t.get("deadline") else "")
        for t in pending_tasks[:15]
    )

    prompt = f"""You are an executive assistant generating a daily email briefing.

Write a concise, professional briefing in plain text (no markdown). Structure:
1. Greeting line
2. Email count and highlights
3. Priority items (urgent/critical emails)
4. Pending tasks
5. Focus recommendation for today

Emails received:
{emails_text or 'No new emails.'}

Pending tasks:
{tasks_text or 'No pending tasks.'}

Keep the briefing under 300 words. Write in second person ("You received...")."""

    return await _call_ai(prompt, max_tokens=1024, creative=True)
