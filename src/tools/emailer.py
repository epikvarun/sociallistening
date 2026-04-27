import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from src import config

SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "varun@getepik.in")


def _build_html(posts: list[dict]) -> str:
    date_str = datetime.now().strftime("%A, %d %B %Y")
    rows = ""
    for i, p in enumerate(posts, 1):
        platform = p.get("platform", "linkedin").capitalize()
        topic = p.get("topic", "")
        text = p.get("text", "")[:300]
        url = p.get("url", "")
        take = p.get("take", "")
        rows += f"""
        <tr style="border-bottom:1px solid #eee;">
          <td style="padding:12px 8px;color:#888;font-size:13px;">{i}</td>
          <td style="padding:12px 8px;">
            <span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">{platform}</span>
            &nbsp;
            <span style="background:#f1f3f4;color:#444;padding:2px 8px;border-radius:4px;font-size:12px;">{topic}</span>
          </td>
          <td style="padding:12px 8px;font-size:14px;color:#333;">{text}</td>
          <td style="padding:12px 8px;">
            <a href="{url}" style="color:#1a73e8;text-decoration:none;font-size:13px;">Open post ↗</a>
          </td>
          <td style="padding:12px 8px;font-size:13px;color:#555;font-style:italic;">"{take}"</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f9f9f9;padding:20px;">
  <div style="max-width:900px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <div style="background:#1a1a2e;padding:28px 32px;">
      <h1 style="color:#fff;margin:0;font-size:22px;">📋 Social Listening Digest</h1>
      <p style="color:#aaa;margin:6px 0 0;font-size:14px;">{date_str} &nbsp;·&nbsp; Top {len(posts)} posts</p>
      <p style="color:#aaa;margin:4px 0 0;font-size:13px;">Topics: Pronto · Snabbit · maid service · home cleaning · robo vacuum</p>
    </div>

    <div style="padding:24px 32px;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#f1f3f4;">
            <th style="padding:10px 8px;text-align:left;font-size:12px;color:#888;">#</th>
            <th style="padding:10px 8px;text-align:left;font-size:12px;color:#888;">PLATFORM · TOPIC</th>
            <th style="padding:10px 8px;text-align:left;font-size:12px;color:#888;">POST PREVIEW</th>
            <th style="padding:10px 8px;text-align:left;font-size:12px;color:#888;">LINK</th>
            <th style="padding:10px 8px;text-align:left;font-size:12px;color:#888;">SUGGESTED COMMENT</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div style="background:#f1f3f4;padding:16px 32px;">
      <p style="margin:0;font-size:13px;color:#666;">
        Open each link → paste the suggested comment → post it.<br>
        <strong>Excel log:</strong> data/social_listening_posts.xlsx
      </p>
    </div>

  </div>
</body>
</html>"""


def send_digest(posts: list[dict], subject: str = None) -> bool:
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("[email] EMAIL_SENDER or EMAIL_PASSWORD not set.")
        return False

    date_str = datetime.now().strftime("%d %b %Y")
    subject = subject or f"Social Listening Digest — {date_str} ({len(posts)} posts)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_TO

    # Plain text fallback
    plain_lines = [f"Social Listening Digest — {date_str}\n"]
    for i, p in enumerate(posts, 1):
        plain_lines.append(
            f"{i}. [{p.get('platform','').upper()}] {p.get('topic','')} | {p.get('url','')}\n"
            f"   Comment: \"{p.get('take','')}\"\n"
        )
    msg.attach(MIMEText("\n".join(plain_lines), "plain"))
    msg.attach(MIMEText(_build_html(posts), "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_TO, msg.as_string())
        print(f"[email] Sent to {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"[email] Failed: {e}")
        return False
