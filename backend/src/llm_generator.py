import os
from dotenv import load_dotenv
import openai

load_dotenv()


class PhishingEmailGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Add it to backend/.env and restart the server."
            )
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def generate(self, scraped_data: dict) -> dict:
        """Generate a personalized phishing email from real scraped data."""

        prompt = self._build_prompt(scraped_data)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity expert demonstrating social engineering "
                        "tactics for educational purposes. Follow the exact output format requested."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        email_text = response.choices[0].message.content
        return self._parse_email(email_text)

    def _build_prompt(self, data: dict) -> str:
        recent_posts = "\n".join(
            f"- {post['text']}" for post in data.get("recent_posts", [])[:5]
        )

        events = data.get("events", [])
        event_context = ""
        if events:
            e = events[0]
            event_context = (
                f"\nRecent Event:\n"
                f"- Name: {e.get('name', 'Unknown')}\n"
                f"- Role: {e.get('role', 'Participant')}\n"
                f"- Date: {e.get('date', 'Recent')}\n"
                f"- Participants: {e.get('participants', 'unknown')}\n"
            )

        connections = ", ".join(
            c["name"] for c in data.get("connections", [])[:3]
        )

        return f"""
You are demonstrating social engineering for cybersecurity education.

TARGET PROFILE DATA (Facebook profile):
Recent Posts:
{recent_posts}

{event_context}

Frequent Connections: {connections if connections else "Not identified"}

Communication Tone: {data.get('tone_analysis', 'professional')}

TASK: Generate a convincing phishing email that:
1. Pretends to be from a friend, event participant, or collaborator visible in the data above.
2. References SPECIFIC details from their Facebook posts (names, events, numbers, quotes).
3. Uses the same tone and writing style as the target.
4. Creates a believable reason to click a link (e.g., event photos, survey, shared document, tagged album).
5. Feels natural and expected, not suspicious.
6. The SENDER_NAME MUST be a Vietnamese name (e.g., Nguyen Minh Tuan, Tran Thi Mai, Le Hoang Nam). Never use English/Western names.
7. Write the email body in English but make the sender identity feel authentically Vietnamese.

FORMAT (use this exact structure):
SUBJECT: [subject line]

BODY:
[greeting]

[paragraph 1: establish credibility by referencing specific details from their posts]

[paragraph 2: create emotional connection and provide call-to-action]

[closing]

SENDER_NAME: [fake but realistic Vietnamese name]
SENDER_EMAIL: [plausible email address using the Vietnamese name]
CTA_TEXT: [text for link button]
LINK_DESCRIPTION: [what the link supposedly leads to]

Generate ONLY the email, nothing else.
"""

    def _parse_email(self, response_text: str) -> dict:
        lines = response_text.strip().split("\n")

        email = {
            "subject": "",
            "body": "",
            "sender_name": "Unknown",
            "sender_email": "contact@example.com",
            "cta_text": "View Document",
            "link_description": "shared document",
        }

        current_section = None
        body_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Strip markdown bold markers the LLM sometimes adds
            clean = stripped.replace("**", "").replace("*", "")

            if clean.startswith("SUBJECT:"):
                email["subject"] = clean.replace("SUBJECT:", "").strip()
            elif clean.startswith("BODY:"):
                current_section = "body"
            elif clean.startswith("SENDER_NAME:"):
                current_section = None
                email["sender_name"] = clean.replace("SENDER_NAME:", "").strip()
            elif clean.startswith("SENDER_EMAIL:"):
                current_section = None
                email["sender_email"] = clean.replace("SENDER_EMAIL:", "").strip()
            elif clean.startswith("CTA_TEXT:"):
                current_section = None
                email["cta_text"] = clean.replace("CTA_TEXT:", "").strip()
            elif clean.startswith("LINK_DESCRIPTION:"):
                current_section = None
                email["link_description"] = clean.replace("LINK_DESCRIPTION:", "").strip()
            elif current_section == "body":
                body_lines.append(line.rstrip())

        email["body"] = "\n\n".join(
            para.strip() for para in "\n".join(body_lines).split("\n\n") if para.strip()
        )

        if not email["subject"] or not email["body"]:
            raise ValueError(
                "LLM response could not be parsed into a valid email. "
                f"Raw response:\n{response_text[:500]}"
            )

        return email
