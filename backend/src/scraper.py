from __future__ import annotations

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
        """Navigate to a Facebook profile and extract everything useful for social engineering."""

        base_url = url.rstrip("/")

        debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug")
        os.makedirs(debug_dir, exist_ok=True)

        # ── 1. Profile page: extract name, intro/bio, and posts ───────
        print(f"[Scraper] Navigating to: {base_url}")
        await self._page.goto(base_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        await self._dismiss_popups()

        await self._page.screenshot(path=os.path.join(debug_dir, "page.png"), full_page=False)

        profile_name = await self._extract_profile_name()
        print(f"[Scraper] Profile name: {profile_name}")
        intro_items = await self._extract_intro_sidebar()

        # Scroll to load posts
        for _ in range(10):
            await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.2)

        # Expand "See more" / "Xem thêm"
        try:
            see_more = self._page.locator(
                'div[role="button"]:has-text("See more"), '
                'div[role="button"]:has-text("Xem thêm")'
            )
            count = await see_more.count()
            for i in range(min(count, 20)):
                try:
                    await see_more.nth(i).click(timeout=1500)
                    await asyncio.sleep(0.3)
                except Exception:
                    continue
            print(f"[Scraper] Expanded {min(count, 20)} 'See more' buttons")
        except Exception:
            pass

        # Save debug HTML
        try:
            html = await self._page.content()
            with open(os.path.join(debug_dir, "page.html"), "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[Scraper] Debug HTML saved ({len(html)} chars)")
        except Exception:
            pass

        posts = await self._extract_posts()

        # ── 2. About page: structured personal info ───────────────────
        about_info = await self._scrape_about_page(base_url)

        # ── 3. Friends page: visible friend names ─────────────────────
        friend_names = await self._scrape_friends_page(base_url, profile_name)

        # ── 4. Analysis ──────────────────────────────────────────────
        connections = self._extract_mentions(posts)
        if friend_names:
            existing = {c["name"] for c in connections}
            for name in friend_names:
                if name not in existing:
                    connections.append({"name": name, "frequency": "friend-list"})

        events = self._extract_events(posts)
        tone = self._analyze_tone(posts)

        if not posts and not about_info and not friend_names:
            raise ValueError(
                f"Could not extract any data from {url}. "
                "The profile may be private, or cookies may be missing/expired. "
                "Export your Facebook cookies to backend/cookies.json and try again."
            )

        return {
            "profile_url": url,
            "profile_name": profile_name,
            "intro": intro_items,
            "about": about_info,
            "recent_posts": [
                {
                    "text": p["text"],
                    "date": p.get("date", "Recent"),
                    "likes": p.get("likes", 0),
                    "comments": p.get("comments", 0),
                }
                for p in posts
            ],
            "connections": connections[:10],
            "events": events,
            "tone_analysis": tone,
        }

    # ── Dismiss popups / overlays ──────────────────────────────────

    async def _dismiss_popups(self):
        """Close notification popups, cookie banners, login dialogs,
        and any other overlays that block the profile content."""

        # Press Escape to close any open overlay (notifications, messenger, etc.)
        for _ in range(3):
            await self._page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

        # Click away from popups by clicking the main content area
        try:
            await self._page.click('div[role="main"]', timeout=2000)
        except Exception:
            pass

        # Close common Facebook dialogs
        close_selectors = [
            'div[aria-label="Close"]',
            'div[aria-label="Đóng"]',
            'a[aria-label="Close"]',
            'a[aria-label="Đóng"]',
        ]
        for selector in close_selectors:
            try:
                btn = self._page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible(timeout=1000):
                    await btn.click(timeout=1500)
                    await asyncio.sleep(0.5)
            except Exception:
                continue

        # Wait a moment for the page to settle
        await asyncio.sleep(1)
        print("[Scraper] Dismissed popups")

    # ── Profile name ─────────────────────────────────────────────────

    async def _extract_profile_name(self) -> str:
        # Try to get profile name from the main content area (not popups/overlays)
        selectors = [
            'div[role="main"] h1',
            'h1',
        ]
        skip_names = {
            "thông báo", "notifications", "messenger", "facebook",
            "watch", "marketplace", "groups", "gaming",
        }
        for selector in selectors:
            try:
                headings = self._page.locator(selector)
                count = await headings.count()
                for i in range(min(count, 5)):
                    name = (await headings.nth(i).inner_text(timeout=2000)).strip()
                    if name and len(name) < 80 and name.lower() not in skip_names:
                        return name
            except Exception:
                continue
        return ""

    # ── Intro sidebar (the short bullet list on the profile page) ────

    async def _extract_intro_sidebar(self) -> list[str]:
        items: list[str] = []
        try:
            intro_section = self._page.locator('div:has(> span:text-is("Intro"))').first
            if await intro_section.count() == 0:
                intro_section = self._page.locator('text="Intro"').locator("..").locator("..")
            spans = await intro_section.locator("li, div[dir='auto']").all()
            for span in spans:
                text = (await span.inner_text(timeout=2000)).strip()
                if text and len(text) > 3 and text != "Intro":
                    items.append(text)
        except Exception:
            pass
        print(f"[Scraper] Intro items: {items}")
        return items[:15]

    # ── About page scraping ──────────────────────────────────────────

    async def _scrape_about_page(self, base_url: str) -> dict:
        about: dict = {}
        sections = [
            ("overview", "overview"),
            ("work_and_education", "work_education"),
            ("places", "places_lived"),
            ("contact_and_basic_info", "contact_info"),
            ("family_and_relationships", "relationships"),
            ("details_about_you", "bio"),
        ]

        for slug, key in sections:
            try:
                url = f"{base_url}/about_overview" if slug == "overview" else f"{base_url}/about_{slug}"
                print(f"[Scraper] Visiting: {url}")
                await self._page.goto(url, timeout=15000, wait_until="domcontentloaded")
                await asyncio.sleep(1.5)

                main_content = self._page.locator('div[role="main"]')
                if await main_content.count() == 0:
                    continue

                raw = await main_content.inner_text(timeout=5000)
                lines = [
                    l.strip() for l in raw.split("\n")
                    if l.strip()
                    and len(l.strip()) > 3
                    and not self._UI_NOISE.match(l.strip())
                    and l.strip() not in ("About", "Overview", "Edit", "Add")
                ]
                if lines:
                    about[key] = lines[:20]
            except Exception as e:
                print(f"[Scraper] About/{slug} failed: {e}")

        print(f"[Scraper] About sections scraped: {list(about.keys())}")
        return about

    # ── Friends page scraping ────────────────────────────────────────

    async def _scrape_friends_page(self, base_url: str, profile_name: str = "") -> list[str]:
        names: list[str] = []
        try:
            friends_url = f"{base_url}/friends"
            print(f"[Scraper] Visiting: {friends_url}")
            await self._page.goto(friends_url, timeout=15000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            for _ in range(3):
                await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(0.8)

            links = await self._page.locator('a[href*="/friends"] span, div[data-visualcompletion="ignore-dynamic"] a[role="link"] span').all()
            for link in links:
                try:
                    text = (await link.inner_text(timeout=1500)).strip()
                    ui_noise = {
                        "friends", "all friends", "mutual friends", "see all",
                        "friend requests", "find friends", "suggestions",
                        "lời mời kết bạn", "tìm bạn bè", "gợi ý",
                        "bạn bè", "tất cả bạn bè", "bạn chung",
                    }
                    if (
                        text
                        and 2 < len(text) < 50
                        and not text.isdigit()
                        and text.lower() not in ui_noise
                        and re.match(r"^[A-ZÀ-ÿ]", text)
                        and text != profile_name
                    ):
                        names.append(text)
                except Exception:
                    continue

            names = list(dict.fromkeys(names))
            print(f"[Scraper] Friends found: {len(names)} — {names[:5]}")
        except Exception as e:
            print(f"[Scraper] Friends page failed: {e}")

        return names[:20]

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
        """Extract posts using data-ad-preview='message' which is where
        Facebook actually renders post text (NOT inside div[role='article'])."""

        js_code = """() => {
            var results = [];
            var debug = [];
            var seenTexts = {};

            var messageDivs = document.querySelectorAll(
                'div[data-ad-preview="message"], div[data-ad-comet-preview="message"]'
            );
            debug.push('Found ' + messageDivs.length + ' data-ad-preview message divs');

            var storyMsgDivs = document.querySelectorAll(
                'div[data-ad-rendering-role="story_message"]'
            );
            debug.push('Found ' + storyMsgDivs.length + ' story_message divs');

            var allMsgNodes = Array.from(messageDivs).concat(Array.from(storyMsgDivs));

            for (var idx = 0; idx < allMsgNodes.length; idx++) {
                var msgDiv = allMsgNodes[idx];
                var postText = (msgDiv.innerText || '').trim();

                if (!postText || postText.length < 5) {
                    debug.push('Msg ' + idx + ': SKIP (too short: ' + postText.length + ')');
                    continue;
                }

                var key = postText.substring(0, 200);
                if (seenTexts[key]) {
                    debug.push('Msg ' + idx + ': SKIP (duplicate)');
                    continue;
                }
                seenTexts[key] = true;

                var card = msgDiv;
                for (var up = 0; up < 25; up++) {
                    if (!card.parentElement) break;
                    card = card.parentElement;
                    if (card.querySelector('div[data-ad-rendering-role="profile_name"]')) {
                        break;
                    }
                }

                var author = '';
                var profileNameDiv = card.querySelector('div[data-ad-rendering-role="profile_name"]');
                if (profileNameDiv) {
                    var authorEl = profileNameDiv.querySelector('a[role="link"] b span span');
                    if (!authorEl) authorEl = profileNameDiv.querySelector('a[role="link"] strong');
                    if (authorEl) {
                        author = (authorEl.innerText || '').trim();
                    }
                    if (!author) {
                        var h2 = profileNameDiv.querySelector('h2, h3');
                        if (h2) author = (h2.innerText || '').trim();
                    }
                }

                var date = 'Recent';
                var ariaLinks = card.querySelectorAll('a[aria-label]');
                for (var li = 0; li < ariaLinks.length; li++) {
                    var label = (ariaLinks[li].getAttribute('aria-label') || '').trim();
                    var dateRe = /january|february|march|april|may|june|july|august|september|october|november|december|yesterday|today|hours? ago|minutes? ago|days? ago|weeks? ago/i;
                    if (dateRe.test(label) || /th.ng|thg/i.test(label)) {
                        date = label;
                        break;
                    }
                }

                if (date === 'Recent') {
                    var postLinks = card.querySelectorAll('a[href*="/posts/"], a[href*="/photo"], a[href*="story_fbid"], a[href*="pfbid"]');
                    for (var pi = 0; pi < postLinks.length; pi++) {
                        var pLabel = (postLinks[pi].getAttribute('aria-label') || '').trim();
                        if (pLabel.length > 3 && pLabel.length < 80) {
                            date = pLabel;
                            break;
                        }
                    }
                }

                var cardText = card.innerText || '';
                var likes = '0';
                var comments = '0';
                var shares = '0';

                var likeM = cardText.match(/(\\d+[KkMm]?)\\s*(?:like|Love|Haha|Wow)/i);
                if (likeM) likes = likeM[1];
                var reactM = cardText.match(/(\\d+[KkMm]?)\\s*(?:reactions?)/i);
                if (reactM) likes = reactM[1];

                var commentM = cardText.match(/(\\d+[KkMm]?)\\s*(?:comments?)/i);
                if (commentM) comments = commentM[1];

                var shareM = cardText.match(/(\\d+[KkMm]?)\\s*(?:shares?)/i);
                if (shareM) shares = shareM[1];

                debug.push('Msg ' + idx + ': author=' + author + ' date=' + date + ' likes=' + likes + ' len=' + postText.length + ' text=' + postText.substring(0, 120));

                results.push({
                    text: postText,
                    author: author,
                    date: date,
                    likes: likes,
                    comments: comments,
                    shares: shares
                });
            }

            if (results.length === 0) {
                debug.push('FALLBACK: searching div[dir=auto] in main content');
                var mainContent = document.querySelector('div[role="main"]');
                if (mainContent) {
                    var autoDivs = mainContent.querySelectorAll('div[dir="auto"]');
                    debug.push('Found ' + autoDivs.length + ' div[dir=auto] in main');
                    for (var fi = 0; fi < autoDivs.length; fi++) {
                        var div = autoDivs[fi];
                        var t = (div.innerText || '').trim();
                        if (t.length < 20) continue;

                        var inForm = false;
                        var p = div.parentElement;
                        while (p) {
                            if (p.tagName === 'FORM' || p.getAttribute('contenteditable')) {
                                inForm = true;
                                break;
                            }
                            p = p.parentElement;
                        }
                        if (inForm) continue;

                        var fKey = t.substring(0, 200);
                        if (seenTexts[fKey]) continue;
                        seenTexts[fKey] = true;

                        results.push({
                            text: t,
                            author: '',
                            date: 'Recent',
                            likes: '0',
                            comments: '0',
                            shares: '0'
                        });
                        debug.push('Fallback post ' + fi + ': ' + t.substring(0, 100));
                        if (results.length >= 15) break;
                    }
                }
            }

            return { posts: results, debug: debug };
        }"""

        raw_posts = await self._page.evaluate(js_code)

        debug_lines = raw_posts.get("debug", [])
        for line in debug_lines:
            print(f"[Scraper/JS] {line}")

        posts = []
        for i, raw in enumerate(raw_posts.get("posts", [])):
            text = raw.get("text", "").strip()
            if not text or len(text) < 5:
                continue
            if self._UI_NOISE.match(text):
                continue

            post = {
                "text": text,
                "author": raw.get("author", ""),
                "date": raw.get("date", "Recent"),
                "likes": self._parse_count(raw.get("likes", "0")),
                "comments": self._parse_count(raw.get("comments", "0")),
                "shares": self._parse_count(raw.get("shares", "0")),
            }
            posts.append(post)
            print(f"[Scraper] Post {i}: author={post['author']!r} date={post['date']!r} ({len(text)} chars): {repr(text[:150])}")

        # Deduplicate: longer text wins
        posts.sort(key=lambda p: len(p["text"]), reverse=True)
        unique: list[dict] = []
        for p in posts:
            text = p["text"].strip()
            if not any(text in existing["text"] for existing in unique):
                unique.append(p)

        print(f"[Scraper] Final unique posts: {len(unique)}")
        return unique[:15]

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
