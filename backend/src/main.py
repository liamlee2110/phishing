from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import uvicorn
import sqlite3

from src.scraper import FacebookScraper
from src.llm_generator import PhishingEmailGenerator
from src.email_sender import send_email

import os

app = FastAPI(title="AI Phishing Demo API")

# Allow all origins by default; set ALLOWED_ORIGINS env var to restrict
# e.g. ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3001
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = PhishingEmailGenerator()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

DB_PATH = "votes.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS votes
           (id INTEGER PRIMARY KEY AUTOINCREMENT, choice TEXT)"""
    )
    conn.commit()
    conn.close()


init_db()


class GenerateRequest(BaseModel):
    profile_url: HttpUrl
    cookies: Optional[List[dict]] = None


class VoteRequest(BaseModel):
    choice: str


class SendEmailRequest(BaseModel):
    to: str
    email_data: dict


@app.post("/api/generate")
async def generate_attack(request: GenerateRequest):
    url = str(request.profile_url)

    scraper = await FacebookScraper.create(cookies_json=request.cookies)
    try:
        scraped_data = await scraper.scrape_profile(url)
    finally:
        await scraper.close()

    email = generator.generate(scraped_data)

    return {
        "success": True,
        "scraped_data": scraped_data,
        "phishing_email": email,
    }


@app.post("/api/send-email")
async def send_phishing_email(request: SendEmailRequest):
    try:
        result = send_email(request.to, request.email_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vote")
async def record_vote(request: VoteRequest):
    if request.choice not in ("click", "suspicious"):
        raise HTTPException(status_code=400, detail="Invalid vote choice")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO votes (choice) VALUES (?)", (request.choice,))
    conn.commit()
    conn.close()

    return {"success": True}


@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM votes")
    total = c.fetchone()[0]

    if total == 0:
        conn.close()
        return {"total": 0, "click": 0, "suspicious": 0, "click_percentage": 0}

    c.execute("SELECT COUNT(*) FROM votes WHERE choice='click'")
    clicks = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM votes WHERE choice='suspicious'")
    suspicious = c.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "click": clicks,
        "suspicious": suspicious,
        "click_percentage": round((clicks / total) * 100) if total > 0 else 0,
    }


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
