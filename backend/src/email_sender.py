import os
import requests
from dotenv import load_dotenv

load_dotenv()

APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "")


def build_html_email(email_data: dict) -> str:
    """Convert the LLM-generated email dict into a clean HTML email body."""

    body_paragraphs = email_data["body"].split("\n\n")
    body_html = "".join(f"<p>{p.strip()}</p>" for p in body_paragraphs if p.strip())

    cta_text = email_data.get("cta_text", "View Document")
    link_desc = email_data.get("link_description", "")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
  {body_html}
  <p>
    <a href="http://localhost:3000/scam">{cta_text}</a>
  </p>
  {f'<p>{link_desc}</p>' if link_desc else ''}
  <br>
  <p>
    <small>This is an educational demonstration — CECS1031 VinUniversity</small>
  </p>
</body>
</html>"""


def send_email(to: str, email_data: dict) -> dict:
    """Send the phishing email via Google Apps Script Gmail relay."""

    if not APPS_SCRIPT_URL:
        raise RuntimeError(
            "APPS_SCRIPT_URL is not set. Deploy the Apps Script web app "
            "and add the URL to backend/.env"
        )

    html_body = build_html_email(email_data)

    payload = {
        "to": to,
        "subject": email_data["subject"],
        "htmlBody": html_body,
        "senderName": email_data.get("sender_name", "Notification"),
    }

    resp = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"Apps Script returned status {resp.status_code}: {resp.text}")

    result = resp.json()
    if result.get("status") != "ok":
        raise RuntimeError(f"Apps Script error: {result.get('error', 'Unknown error')}")

    return {"success": True, "message": f"Email sent to {to}"}
