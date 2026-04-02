import asyncio
import json
import os
import re
from typing import List, Optional
from playwright.async_api import async_playwright

COOKIES_PATH = os.getenv(
    "FACEBOOK_COOKIES_FILE",
    os.path.join(os.path.dirname(__file__), "..", "cookies.json"),
)


class FacebookScraper:
    """Async Facebook profile scraper using Playwright."""

    def __init__(self):
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    @classmethod
    async def create(
        cls,
        cookies_file: str = None,
        cookies_json: Optional[List[dict]] = None,
        headless: bool = True,
    ):
        """Create a scraper instance.

        If `cookies_json` is provided (list of cookie dicts from Cookie-Editor),
        it takes priority over the cookies file on disk.
        """
        self = cls()
        self._cookies_file = cookies_file or COOKIES_PATH
        self._cookies_json = cookies_json

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--disable-setuid-sandbox",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-software-rasterizer",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        await self._load_cookies()
        self._page = await self._context.new_page()
        return self

    # ── Cookie loading ───────────────────────────────────────────────

    _SAME_SITE_MAP = {
        "no_restriction": "None",
        "lax": "Lax",
        "strict": "Strict",
        "none": "None",
        "None": "None",
        "Lax": "Lax",
        "Strict": "Strict",
    }

    async def _load_cookies(self):
        if self._cookies_json:
            raw_cookies = self._cookies_json
            print(f"[Scraper] Using {len(raw_cookies)} cookies from request body")
        elif os.path.exists(self._cookies_file):
            with open(self._cookies_file, "r") as f:
                raw_cookies = json.load(f)
        else:
            print(
                f"[Scraper] No cookies file at {self._cookies_file}. "
                "Scraping as unauthenticated — most content will be behind a login wall."
            )
            return

        normalized = []
        for c in raw_cookies:
            cookie: dict = {
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ".facebook.com"),
                "path": c.get("path", "/"),
            }

            raw_ss = c.get("sameSite")
            cookie["sameSite"] = self._SAME_SITE_MAP.get(raw_ss or "", "None")

            if c.get("secure"):
                cookie["secure"] = True
            if c.get("httpOnly"):
                cookie["httpOnly"] = True
            if c.get("expirationDate"):
                cookie["expires"] = c["expirationDate"]

            normalized.append(cookie)

        await self._context.add_cookies(normalized)
        print(f"[Scraper] Loaded {len(normalized)} cookies from {self._cookies_file}")

    # ── Main scrape ──────────────────────────────────────────────────

    async def scrape_profile(self, url: str) -> dict:
        """Navigate to a Facebook profile and extract posts, connections, events, and tone."""

        print(f"[Scraper] Navigating to: {url}")
        await self._page.goto(url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Save a debug screenshot so we can see what the page looks like
        debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        await self._page.screenshot(path=os.path.join(debug_dir, "page.png"), full_page=False)
        print(f"[Scraper] Debug screenshot saved to backend/debug/page.png")

        for _ in range(3):
            await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)

        posts = await self._extract_posts()

        if not posts:
            raise ValueError(
                f"Could not extract any posts from {url}. "
                "The profile may be private, or cookies may be missing/expired. "
                "Export your Facebook cookies to backend/cookies.json and try again."
            )

        connections = self._extract_mentions(posts)
        events = self._extract_events(posts)
        tone = self._analyze_tone(posts)

        return {
            "profile_url": url,
            "recent_posts": [
                {
                    "text": p["text"],
                    "date": p.get("date", "Recent"),
                    "likes": p.get("likes", 0),
                    "comments": p.get("comments", 0),
                }
                for p in posts
            ],
            "connections": connections,
            "events": events,
            "tone_analysis": tone,
        }

    # ── Post extraction ──────────────────────────────────────────────

    _UI_NOISE = re.compile(
        r"^("
        r"Like|Comment|Share|Send|Reply|See more|See less|See translation"
        r"|Top comments|Most relevant|Newest first|All comments"
        r"|Write a comment.*|Press enter.*"
        r"|Haha|Love|Wow|Sad|Angry|Care"
        r"|.*shared a (post|photo|link|memory|reel|video).*"
        r"|View \d+ more comment.*"
        r"|\d+ (likes?|comments?|shares?|views?)"
        r"|\d+[KkMm]?\s*(likes?|comments?|shares?|views?)"
        r")$",
        re.IGNORECASE,
    )

    async def _extract_posts(self) -> list:
        posts = []

        # Strategy 1: div[role="article"] (standard Facebook post containers)
        articles = await self._page.locator('div[role="article"]').all()
        print(f"[Scraper] Found {len(articles)} article elements")

        for i, article in enumerate(articles):
            try:
                raw_text = await article.inner_text(timeout=5000)
            except Exception:
                continue

            print(f"[Scraper] Article {i} raw text ({len(raw_text)} chars): {repr(raw_text[:300])}")

            cleaned = self._clean_article_text(raw_text)
            print(f"[Scraper] Article {i} cleaned ({len(cleaned)} chars): {repr(cleaned[:200])}")

            if cleaned and len(cleaned) > 20:
                post = {"text": cleaned, "date": "Recent", "likes": 0, "comments": 0}

                likes_match = re.search(r"(\d+[KkMm]?)\s*(?:likes?|Love|Haha|Wow)", raw_text)
                if likes_match:
                    post["likes"] = self._parse_count(likes_match.group(1))

                comments_match = re.search(r"(\d+[KkMm]?)\s*comments?", raw_text, re.I)
                if comments_match:
                    post["comments"] = self._parse_count(comments_match.group(1))

                posts.append(post)

        # Strategy 2: If no articles found, try extracting from div[dir="auto"] (Facebook user text)
        if not posts:
            print("[Scraper] No posts from articles, trying div[dir='auto'] fallback...")
            auto_divs = await self._page.locator('div[dir="auto"]').all()
            print(f"[Scraper] Found {len(auto_divs)} div[dir='auto'] elements")

            for div in auto_divs:
                try:
                    text = await div.inner_text(timeout=2000)
                    text = text.strip()
                except Exception:
                    continue

                if len(text) > 30 and not self._UI_NOISE.match(text):
                    posts.append({"text": text, "date": "Recent", "likes": 0, "comments": 0})

        # Strategy 3: Last resort — grab large text blocks from the full page
        if not posts:
            print("[Scraper] No posts from div[dir='auto'], trying full page text extraction...")
            full_text = await self._page.inner_text("body")
            paragraphs = full_text.split("\n")
            for para in paragraphs:
                para = para.strip()
                if len(para) > 50 and not self._UI_NOISE.match(para):
                    posts.append({"text": para, "date": "Recent", "likes": 0, "comments": 0})

        # Deduplicate: remove posts that are substrings of longer posts
        posts.sort(key=lambda p: len(p["text"]), reverse=True)
        unique: list[dict] = []
        for p in posts:
            text = p["text"].strip()
            if not any(text in existing["text"] for existing in unique):
                unique.append(p)

        print(f"[Scraper] Extracted {len(unique)} unique posts total")
        return unique[:10]

    def _clean_article_text(self, raw: str) -> str:
        lines = raw.split("\n")
        kept: list[str] = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 4:
                continue
            if self._UI_NOISE.match(line):
                continue
            if re.match(
                r"^(\d+[hms]|Yesterday|Just now|\d+ (hours?|minutes?|days?|weeks?) ago)$",
                line, re.I,
            ):
                continue
            kept.append(line)
        return " ".join(kept)

    @staticmethod
    def _parse_count(s: str) -> int:
        s = s.strip().upper()
        if s.endswith("K"):
            return int(float(s[:-1]) * 1_000)
        if s.endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        try:
            return int(s)
        except ValueError:
            return 0

    # ── Mention / connection extraction ──────────────────────────────

    def _extract_mentions(self, posts: list) -> list:
        mention_counts: dict[str, int] = {}

        for post in posts:
            text = post["text"]

            for m in re.findall(r"@(\w[\w ]{1,30})", text):
                self._count_name(mention_counts, m)

            for m in re.findall(
                r"(?:with|cùng|và|and)\s+([A-Z][a-zÀ-ÿ]+(?:\s[A-Z][a-zÀ-ÿ]+){0,3})", text
            ):
                self._count_name(mention_counts, m)

            for m in re.findall(
                r"(?:thanks? to|shoutout to|shout out to|grateful to|credit to|appreciate)\s+"
                r"([A-Z][a-zÀ-ÿ]+(?:\s[A-Z][a-zÀ-ÿ]+){0,3})",
                text, re.IGNORECASE,
            ):
                self._count_name(mention_counts, m)

        connections = []
        for name, count in sorted(mention_counts.items(), key=lambda x: -x[1]):
            freq = "high" if count >= 3 else "medium" if count >= 2 else "low"
            connections.append({"name": name, "frequency": freq})

        return connections[:5]

    @staticmethod
    def _count_name(counts: dict, raw_name: str):
        name = raw_name.strip()
        if 2 < len(name) < 40:
            counts[name] = counts.get(name, 0) + 1

    # ── Event extraction ─────────────────────────────────────────────

    _EVENT_PATTERNS = [
        re.compile(
            r"(?:attended|joined|organized|hosted|participated in|went to|"
            r"checked in at|volunteered at|spoke at|presented at)\s+(.+?)(?:[.!?\n]|$)",
            re.IGNORECASE,
        ),
        re.compile(
            r"((?:hackathon|conference|workshop|meetup|seminar|festival|competition|"
            r"ceremony|summit|bootcamp|expo|gala|marathon|concert|webinar)"
            r"[\s:]+.+?)(?:[.!?\n]|$)",
            re.IGNORECASE,
        ),
    ]

    _EVENT_KEYWORDS = frozenset([
        "hack", "fest", "con", "summit", "meet", "workshop", "day", "week",
        "gala", "expo", "boot", "marathon", "jam", "sprint",
    ])

    def _extract_events(self, posts: list) -> list:
        events: list[dict] = []

        for post in posts:
            text = post["text"]

            for pattern in self._EVENT_PATTERNS:
                for match in pattern.findall(text):
                    name = match.strip()[:80]
                    if len(name) > 5:
                        events.append({
                            "name": name,
                            "role": "Participant",
                            "date": post.get("date", "Recent"),
                            "participants": "Unknown",
                        })

            for m in re.findall(r"([A-Z][a-zÀ-ÿ]+(?:\s[A-Z][a-zÀ-ÿ]+){1,5}(?:\s\d{4})?)", text):
                if any(kw in m.lower() for kw in self._EVENT_KEYWORDS):
                    events.append({
                        "name": m.strip(),
                        "role": "Mentioned",
                        "date": post.get("date", "Recent"),
                        "participants": "Unknown",
                    })

        seen: set[str] = set()
        unique: list[dict] = []
        for e in events:
            if e["name"] not in seen:
                seen.add(e["name"])
                unique.append(e)

        return unique[:5]

    # ── Tone analysis ────────────────────────────────────────────────

    def _analyze_tone(self, posts: list) -> str:
        all_text = " ".join(p["text"] for p in posts).lower()
        word_count = len(all_text.split())
        if word_count == 0:
            return "neutral"

        traits: list[str] = []

        if all_text.count("!") / max(len(posts), 1) > 1.0:
            traits.append("enthusiastic")

        informal = ["i'm", "i've", "don't", "can't", "won't", "gonna", "wanna",
                     "lol", "haha", "omg", "ngl", "tbh", "fr"]
        formal = ["furthermore", "therefore", "regarding", "pleased to",
                  "delighted", "sincerely", "accordingly"]
        inf_score = sum(1 for w in informal if w in all_text)
        frm_score = sum(1 for w in formal if w in all_text)
        if frm_score > inf_score:
            traits.append("formal")
        elif inf_score > frm_score:
            traits.append("casual")

        positive = ["great", "amazing", "wonderful", "fantastic", "love", "excellent",
                     "awesome", "happy", "excited", "grateful", "thank", "best",
                     "incredible", "proud", "blessed", "thrilled"]
        negative = ["bad", "terrible", "hate", "awful", "worst", "frustrated",
                     "disappointed", "angry", "sad", "unfortunately"]
        pos = sum(all_text.count(w) for w in positive)
        neg = sum(all_text.count(w) for w in negative)
        if pos > neg * 2:
            traits.append("positive")
        elif neg > pos:
            traits.append("negative")

        if sum(all_text.count(w) for w in ["thank", "grateful", "appreciate", "blessed"]) >= 2:
            traits.append("grateful")

        prof = ["project", "team", "milestone", "achievement", "collaboration",
                "opportunity", "career", "learning", "growth", "mentor"]
        if sum(all_text.count(w) for w in prof) >= 3:
            traits.append("professional")

        emoji_re = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            r"\U00002702-\U000027B0\U0001F900-\U0001F9FF]"
        )
        if len(emoji_re.findall(all_text)) > 3:
            traits.append("emoji-heavy")

        return ", ".join(traits) if traits else "neutral, analytical"

    # ── Cleanup ──────────────────────────────────────────────────────

    async def close(self):
        try:
            await self._context.close()
            await self._browser.close()
            await self._pw.stop()
        except Exception:
            pass
