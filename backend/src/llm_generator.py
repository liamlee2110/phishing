import os
import re
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
            max_tokens=5000,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity expert demonstrating social engineering "
                        "tactics for educational purposes. Follow the exact output format requested. "
                        "You MUST write everything in English regardless of the target's language."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        email_text = response.choices[0].message.content
        return self._parse_email(email_text)

    def _build_prompt(self, data: dict) -> str:
        # Profile identity
        profile_name = data.get("profile_name", "Unknown")

        # Intro sidebar items (work, education, location, etc.)
        intro = data.get("intro", [])
        intro_text = "\n".join(f"- {item}" for item in intro) if intro else "Not available"

        # About page structured data
        about = data.get("about", {})
        about_sections: list[str] = []
        for key, items in about.items():
            label = key.replace("_", " ").title()
            about_sections.append(f"{label}:\n" + "\n".join(f"  - {i}" for i in items[:10]))
        about_text = "\n\n".join(about_sections) if about_sections else "Not available"

        # Posts
        recent_posts = "\n".join(
            f"- {post['text']}" for post in data.get("recent_posts", [])[:10]
        )

        # Events
        events = data.get("events", [])
        events_text = ""
        if events:
            events_text = "\nRecent Events:\n" + "\n".join(
                f"- {e.get('name', 'Unknown')} (role: {e.get('role', 'Participant')}, date: {e.get('date', 'Recent')})"
                for e in events[:5]
            )

        # Connections & friends
        connections = data.get("connections", [])
        conn_text = ", ".join(
            f"{c['name']} ({c.get('frequency', 'unknown')})" for c in connections[:10]
        ) if connections else "Not identified"

        return f"""
You are demonstrating social engineering for cybersecurity education.

TARGET PROFILE DATA (Facebook):

Profile Name: {profile_name}

Intro (sidebar):
{intro_text}

About (detailed):
{about_text}

Recent Posts:
{recent_posts if recent_posts else "No posts extracted"}
{events_text}

Known Connections / Friends: {conn_text}

Communication Tone: {data.get('tone_analysis', 'professional')}

IMPORTANT: The ENTIRE email MUST be written in ENGLISH. Even if the target's posts are in Vietnamese or another language, translate and adapt everything into natural English. Never write the subject, body, or CTA in any language other than English.

TASK: Generate the most convincing, hyper-personalized phishing email possible:
1. Impersonate someone from the target's ACTUAL friend list or connections above. Use their real name.
2. Reference SPECIFIC details: workplace, school, events, hobbies, recent posts, location, relationships — anything scraped above.
3. Match the target's energy and style (formal/casual/emoji-heavy/etc.) but ALWAYS in English.
4. Create a believable, urgent reason to click a link (event photos, shared doc, tagged album, scholarship result, work document, reunion invite).
5. The email must feel like it could genuinely come from someone the target knows.
6. The sender should have a culturally appropriate name matching the target's background (e.g., Vietnamese name for Vietnamese targets).
7. Include small personal touches that prove "insider knowledge" (mentioning a mutual friend, a specific event they attended, their workplace).

CRITICAL FORMATTING RULES:
- The BODY must be PLAIN TEXT only. NO URLs, NO links, NO markdown syntax.
- Do NOT put any "[Click here](url)" or "http://..." in the body. The link is added separately via CTA_TEXT.
- The body should read like a normal email a friend would write — just text, no hyperlinks.
- Do NOT repeat the call-to-action link text inside the body. Just reference the action naturally (e.g., "I put together an album, check it out below").

FORMAT (use this exact structure):
SUBJECT: [subject line]

BODY:
[greeting — use the target's first name]

[paragraph 1: establish credibility by referencing specific personal details]

[paragraph 2: create emotional connection or urgency, and naturally mention what the link is for WITHOUT including any URL]

[paragraph 3 (optional): add another personal reference to reinforce trust]

[closing with sender's name]

SENDER_NAME: [a real name from their friend list/connections, or a realistic fake one]
SENDER_EMAIL: [plausible email address using the sender name]
CTA_TEXT: [text for the link button — make it specific, not generic]
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

        raw_body = "\n\n".join(
            para.strip() for para in "\n".join(body_lines).split("\n\n") if para.strip()
        )

        # Strip markdown links: [text](url) → text
        raw_body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw_body)
        # Strip bare URLs
        raw_body = re.sub(r"https?://\S+", "", raw_body)
        # Clean up leftover parentheses/brackets from stripped links
        raw_body = re.sub(r"\(\s*\)", "", raw_body)
        # Collapse multiple spaces
        raw_body = re.sub(r"  +", " ", raw_body)

        email["body"] = raw_body.strip()

        if not email["subject"] or not email["body"]:
            raise ValueError(
                "LLM response could not be parsed into a valid email. "
                f"Raw response:\n{response_text[:500]}"
            )

        return email
