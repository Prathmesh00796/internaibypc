"""
Notification service: dispatches to email / Telegram / Discord based
on Notification.channel. Called from Celery tasks (see app.workers.notification_tasks)
so sending never blocks the request/response cycle.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import settings
from app.core.logging_config import logger


def send_email(to_email: str, subject: str, body_html: str) -> None:
    if not settings.SMTP_HOST:
        logger.info(f"[email disabled] Would send to {to_email}: {subject}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())


def send_telegram(chat_id: str, text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info(f"[telegram disabled] Would send to {chat_id}: {text}")
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        httpx.post(url, json={"chat_id": chat_id, "text": text}, timeout=10.0)
    except httpx.HTTPError as exc:
        logger.error(f"Telegram send failed: {exc}")


def send_discord(webhook_url: str, content: str) -> None:
    try:
        httpx.post(webhook_url, json={"content": content}, timeout=10.0)
    except httpx.HTTPError as exc:
        logger.error(f"Discord send failed: {exc}")


NOTIFICATION_TEMPLATES = {
    "new_job": lambda ctx: (
        f"🎯 New match: {ctx['job_title']} at {ctx['company']} ({ctx['match_score']}% match)",
        f"<p>A new internship matches your profile:</p><p><b>{ctx['job_title']}</b> at {ctx['company']}</p>"
        f"<p>Match score: {ctx['match_score']}%</p><p><a href='{ctx['url']}'>View details</a></p>",
    ),
    "interview": lambda ctx: (
        f"📅 Interview scheduled: {ctx['job_title']} at {ctx['company']}",
        f"<p>Your application for <b>{ctx['job_title']}</b> at {ctx['company']} has moved to interview stage.</p>",
    ),
    "offer": lambda ctx: (
        f"🎉 Offer received: {ctx['job_title']} at {ctx['company']}",
        f"<p>Congratulations! You've received an offer for <b>{ctx['job_title']}</b> at {ctx['company']}.</p>",
    ),
    "rejection": lambda ctx: (
        f"Update on {ctx['job_title']} at {ctx['company']}",
        f"<p>Your application for <b>{ctx['job_title']}</b> at {ctx['company']} was not selected this time.</p>",
    ),
    "daily_report": lambda ctx: (
        f"📊 Your daily InternAI report — {ctx['new_jobs']} new matches",
        f"<p>{ctx['new_jobs']} new jobs found, {ctx['pending_review']} pending your review.</p>",
    ),
}
