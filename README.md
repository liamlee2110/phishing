# AI Phishing Framework

Educational demo showing how LLMs can weaponize public social media data to craft hyper-personalized phishing emails. Built for cybersecurity awareness presentations.

## Architecture

- **Backend** — Python / FastAPI, Playwright (Facebook scraping), OpenAI GPT-4o Mini (email generation)
- **Frontend** — Next.js / React, Tailwind CSS, shadcn/ui
- **Email relay** — Google Apps Script (Gmail API)

## Prerequisites

- Python 3.9+
- Node.js 18+ and pnpm
- An OpenAI API key
- (Optional) A deployed Google Apps Script web app for sending real emails

## Quick Start

```bash
# 1. Clone and enter the repo
cd phishing

# 2. Copy the env template and fill in your keys
cp backend/.env.example backend/.env
# Edit backend/.env — set OPENAI_API_KEY (required) and APPS_SCRIPT_URL (optional)

# 3. Run everything
chmod +x run_demo.sh
./run_demo.sh
```

This starts both servers:

| Service  | URL                     |
|----------|-------------------------|
| Frontend | http://localhost:3000    |
| Backend  | http://localhost:8000    |

## Manual Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd src
pnpm install
pnpm dev
```

## Facebook Cookies

The scraper needs an authenticated Facebook session. Two options:

1. **Paste at runtime** — On the home page, expand "Facebook Cookies", paste the JSON exported from the [Cookie-Editor](https://cookie-editor.com/) browser extension. Best for live demos since cookies expire frequently.

2. **File on disk** — Save the Cookie-Editor JSON export to `backend/cookies.json`. The scraper reads this automatically if no cookies are provided via the UI.

## Email Sending (Optional)

To demo sending a real phishing email to your own inbox:

1. Create a Google Apps Script project at https://script.google.com
2. Add a `doPost(e)` function that sends email via `GmailApp.sendEmail`
3. Deploy as a web app (execute as yourself, access: anyone)
4. Set `APPS_SCRIPT_URL` in `backend/.env` to the deployed URL
5. On the demo results page, click "Send to Real Inbox" and enter your email

## Usage

1. Open http://localhost:3000
2. Enter a Facebook profile URL (e.g. `https://facebook.com/username`)
3. (Optional) Paste fresh cookies from Cookie-Editor
4. Click **Run** — the system scrapes the profile, analyzes tone, and generates a personalized phishing email
5. Review the scraped data and generated email side by side on the results page

## Disclaimer

This tool is for **educational and authorized security awareness purposes only**. Do not use it to target individuals without their explicit consent. The authors are not responsible for misuse.
