# Project 1: Hyper-Personalized AI Phishing Demonstration
## VinUniversity CECS1031 - Computational & Algorithmic Thinking

---

## 🎯 PROJECT MISSION

**Objective:** Demonstrate how AI systems can weaponize publicly available social media data to create hyper-personalized phishing attacks that are 20x more effective than traditional methods.

**Deliverables:**
- Live demonstration at VinUniversity showcase (semi-public event, open to faculty)
- 4-5 page academic report with figures and references
- Poster presentation (dimensions TBD)
- Audience voting for "Favorite Presentation" (extra credit opportunity)

**Due Date:** [INSERT FROM CANVAS - confirm with professor]

**Team Size:** 5 members

---

## 📋 PROJECT REQUIREMENTS (Official)

From CECS1031 Project Description:

### Expected Outcomes
1. **Presentation (50%)**
   - Format: Poster presentation
   - Location: 2nd Floor, I Building (tentative)
   - **Live demonstration is required**
   - Semi-public academic showcase
   - Possible "Favorite Presentation" vote

2. **Report (50%)**
   - Length: 4-5 pages
   - Required sections:
     - Background of the threat
     - Demonstration explanation
     - Risk analysis
     - Proposed protective measures
     - Key lessons learned

### Critical Requirements
- **Experience or simulate** a threat scenario (not just conceptual understanding)
- **Demonstrate it in class** with live demo
- Propose practical protective/preventive measures
- Demonstrate critical thinking and originality
- Avoid superficial summaries
- Show real understanding, not just description
- Clearly connect theory to practice
- Cite credible academic and industry sources
- ⚠️ **Avoid "infomercial-style" or purely AI-generated reports**
- Speak in your own voice and clearly explain what you personally learned

---

## 🎭 ATTACK SCENARIO

### Target Profile
**VinUniversity Student Competition Organizer**
- Active LinkedIn presence
- Recently organized "VinHack 2026" technology competition
- Posted about: event dates, participant count (120), co-organizer names, results
- Uses LinkedIn for professional networking and career development

### Attack Workflow
```
LinkedIn Profile URL
         ↓
    Web Scraper (Beautiful Soup + Selenium)
         ↓
    Extract: Posts, Connections, Events, Tone
         ↓
    LLM Analysis (Claude 3.5 Sonnet API)
         ↓
    Generate: Personalized Phishing Email
         ↓
    Email Template System (HTML)
         ↓
    Display in Mock Inbox
         ↓
    Audience Vote: "Would You Click?"
```

### Example Attack
**Real LinkedIn Post:**
> "Thank you to all 120 participants who joined VinHack 2026! Special shoutout to the organizing team @NguyenAnh for making this happen. Can't wait for next year!"

**AI-Generated Phishing Email:**
> Subject: Thank You for VinHack 2026!
> 
> Hi [Name],
> 
> I was one of the **120 participants** in VinHack 2026, and I wanted to personally thank you and **@NguyenAnh** for organizing such an amazing event. I've put together a detailed thank-you note for the team—you can read it here: [malicious link]
> 
> Best regards,
> [Fake participant name]

**Why It Works:**
- ✅ References exact participant count (120)
- ✅ Mentions co-organizer by name (@NguyenAnh)
- ✅ Uses same enthusiastic tone as target
- ✅ Arrives shortly after event (psychological timing)
- ✅ Plausible pretext (gratitude expected)
- ✅ Perfect grammar (no red flags)

---

## 🏗️ TECHNICAL ARCHITECTURE

### System Components

#### 1. **Web Scraper Module** (`scraper.py`)
**Technology:** Python + Beautiful Soup + Selenium

**Input:** LinkedIn profile URL

**Output:** JSON file with:
```json
{
  "profile_url": "https://linkedin.com/in/target",
  "recent_posts": [
    {
      "text": "Thank you to all 120 participants...",
      "date": "2025-10-20",
      "likes": 45,
      "comments": 12
    }
  ],
  "connections": [
    {"name": "Nguyen Anh", "frequency": "high"},
    {"name": "Tran Van A", "frequency": "medium"}
  ],
  "events": [
    {
      "name": "VinHack 2026",
      "role": "Organizer",
      "date": "2025-10-15",
      "participants": 120
    }
  ],
  "tone_analysis": "enthusiastic, professional, grateful",
  "writing_style": "formal with exclamation marks"
}
```

**Key Functions:**
- `scrape_profile(url)` - Main entry point
- `extract_posts(driver, count=10)` - Get recent posts
- `extract_connections(driver, count=5)` - Get frequent collaborators
- `extract_events(driver)` - Get organized/attended events
- `analyze_tone(posts)` - Determine communication style

**Implementation Notes:**
- Use Selenium WebDriver for dynamic content
- Handle LinkedIn login wall (may need authenticated session)
- Implement rate limiting to avoid detection
- Error handling for private profiles
- Respect robots.txt and ethical boundaries

---

#### 2. **LLM Analysis Module** (`llm_generator.py`)
**Technology:** Anthropic Claude API (Claude 3.5 Sonnet)

**Input:** JSON data from scraper

**Output:** Personalized phishing email (text)

**API Configuration:**
```python
import anthropic

client = anthropic.Anthropic(
    api_key="YOUR_API_KEY_HERE"  # Store in .env file
)

PROMPT_TEMPLATE = """
You are simulating a social engineering attack for educational purposes.

Given this social media data about a target:
{scraped_data}

Generate a convincing phishing email that:
1. Pretends to be from a participant/attendee of their recent event
2. References specific details (participant count, co-organizer names, event dates)
3. Uses the same tone and writing style as the target
4. Creates a plausible reason for clicking a link (e.g., thank-you document, survey)
5. Includes perfect grammar and natural language

Format the email with:
- Subject line
- Greeting
- Body (2-3 paragraphs)
- Call-to-action with link placeholder
- Closing

Make it feel authentic and expected, not suspicious.
"""
```

**Key Functions:**
- `generate_phishing_email(scraped_data)` - Main generation
- `analyze_context(data)` - Extract key details
- `match_tone(posts)` - Replicate writing style
- `create_pretext(events)` - Generate believable scenario

**Implementation Notes:**
- Use Claude 3.5 Sonnet for best reasoning
- Set `max_tokens=1500` for email length
- Temperature=0.7 for natural variation
- Store API key in environment variable
- Cost: ~$0.002 per email (very cheap)

---

#### 3. **Email Template System** (`email_generator.py`)
**Technology:** Python + Jinja2 + HTML/CSS

**Input:** LLM-generated text

**Output:** Formatted HTML email

**Template Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .email-container { max-width: 600px; margin: 0 auto; }
        .header { background: #f4f4f4; padding: 10px; }
        .body { padding: 20px; }
        .cta-button { 
            background: #0066cc; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            From: {{ sender_name }} &lt;{{ sender_email }}&gt;
        </div>
        <div class="body">
            <p>{{ greeting }}</p>
            {{ email_body }}
            <p><a href="{{ malicious_link }}" class="cta-button">{{ cta_text }}</a></p>
            <p>{{ closing }}</p>
        </div>
    </div>
</body>
</html>
```

**Key Functions:**
- `format_email(text, template)` - Apply HTML template
- `spoof_sender(target_data)` - Create convincing sender address
- `embed_tracking_pixel()` - (Optional) Track if email opened
- `generate_fake_link()` - Create realistic-looking URL

---

#### 4. **Demo Interface** (`demo_ui.py`)
**Technology:** Flask + HTML/CSS/JavaScript

**Purpose:** 
- Display mock inbox showing phishing email
- Interactive audience voting ("Would you click?")
- Live scraping and generation during presentation

**Key Pages:**

**Page 1: Input Form**
```html
<form>
    <input type="url" name="linkedin_url" placeholder="Enter LinkedIn Profile URL">
    <button>Generate Phishing Attack</button>
</form>
```

**Page 2: Loading Animation**
```
Phase 1: Scraping profile... ✓
Phase 2: Analyzing posts... ✓
Phase 3: Generating email... ✓
Phase 4: Formatting message... ✓
```

**Page 3: Side-by-Side Comparison**
```
[LinkedIn Post]  |  [AI-Generated Email]
Real content     |  Personalized phishing
```

**Page 4: Mock Inbox**
```
Inbox (3)
─────────────────────────────────
★ Thank You for VinHack 2026!
  [Fake Participant Name]
  "I was one of the 120 participants..."
  [2 hours ago]
─────────────────────────────────
```

**Page 5: Audience Voting**
```
If you received this email, would you click the link?

[Yes, I would click] [No, seems suspicious]

Results: 73% would click | 27% suspicious
```

---

## 📁 PROJECT STRUCTURE

```
ai-phishing-demo/
│
├── src/
│   ├── scraper.py              # LinkedIn scraping module
│   ├── llm_generator.py        # Claude API integration
│   ├── email_generator.py      # HTML email formatting
│   ├── demo_ui.py              # Flask web interface
│   └── utils.py                # Helper functions
│
├── templates/
│   ├── index.html              # Input form
│   ├── loading.html            # Progress animation
│   ├── comparison.html         # Side-by-side view
│   ├── inbox.html              # Mock email inbox
│   └── voting.html             # Audience poll
│
├── static/
│   ├── css/
│   │   └── style.css           # UI styling
│   ├── js/
│   │   └── voting.js           # Interactive voting
│   └── images/
│       └── linkedin-logo.png
│
├── data/
│   ├── sample_profiles.json    # Test data
│   └── results.json            # Demo day results
│
├── docs/
│   ├── report.docx             # 4-5 page report
│   ├── poster.pptx             # Presentation poster
│   └── references.bib          # APA7 citations
│
├── tests/
│   ├── test_scraper.py
│   ├── test_llm.py
│   └── test_integration.py
│
├── .env                        # API keys (DO NOT COMMIT)
├── .gitignore
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── run_demo.sh                 # Launch script
```

---

## 🛠️ IMPLEMENTATION GUIDE

### Phase 1: Environment Setup (Week 1)

**Install Dependencies:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install beautifulsoup4 selenium anthropic flask jinja2 python-dotenv

# Install Chrome WebDriver
# Download from: https://chromedriver.chromium.org/
```

**Create `.env` file:**
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
CHROME_DRIVER_PATH=/path/to/chromedriver
```

---

### Phase 2: Build Scraper (Week 1)

**File: `src/scraper.py`**

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import time

class LinkedInScraper:
    def __init__(self, driver_path):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in background
        self.driver = webdriver.Chrome(driver_path, options=options)
    
    def scrape_profile(self, url):
        """
        Main scraping function
        Returns: dict with posts, connections, events, tone
        """
        self.driver.get(url)
        time.sleep(3)  # Wait for page load
        
        data = {
            'profile_url': url,
            'recent_posts': self._extract_posts(),
            'connections': self._extract_connections(),
            'events': self._extract_events(),
            'tone_analysis': self._analyze_tone(),
        }
        
        return data
    
    def _extract_posts(self, count=10):
        """Extract recent posts from activity section"""
        posts = []
        
        # Find post elements (adjust selectors based on LinkedIn's HTML)
        post_elements = self.driver.find_elements(
            By.CSS_SELECTOR, 
            'div.feed-shared-update-v2'
        )[:count]
        
        for elem in post_elements:
            try:
                text = elem.find_element(
                    By.CSS_SELECTOR, 
                    'span.break-words'
                ).text
                
                # Extract metadata
                date = elem.find_element(
                    By.CSS_SELECTOR, 
                    'time'
                ).get_attribute('datetime')
                
                posts.append({
                    'text': text,
                    'date': date,
                    'length': len(text)
                })
            except:
                continue
        
        return posts
    
    def _extract_connections(self, count=5):
        """Extract frequently mentioned connections"""
        # Implementation: Parse mentions in posts
        # Look for @mentions or tagged collaborators
        connections = []
        # ... logic here ...
        return connections
    
    def _extract_events(self):
        """Extract organized/attended events"""
        # Implementation: Look for event posts
        events = []
        # ... logic here ...
        return events
    
    def _analyze_tone(self):
        """Simple tone analysis from posts"""
        # Count exclamation marks, positive words, formality level
        # Return: "enthusiastic, professional, grateful"
        return "enthusiastic"
    
    def close(self):
        self.driver.quit()

# Usage example
if __name__ == "__main__":
    scraper = LinkedInScraper('/path/to/chromedriver')
    data = scraper.scrape_profile('https://linkedin.com/in/target')
    
    # Save to file
    with open('scraped_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    scraper.close()
```

**Testing Checklist:**
- [ ] Scrapes at least 5 recent posts
- [ ] Extracts event participation data
- [ ] Identifies co-organizers/frequent collaborators
- [ ] Handles private profiles gracefully (error message)
- [ ] Outputs valid JSON
- [ ] Runs in <30 seconds per profile

---

### Phase 3: Build LLM Generator (Week 1-2)

**File: `src/llm_generator.py`**

```python
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

class PhishingEmailGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.model = "claude-sonnet-4-20250514"
    
    def generate(self, scraped_data):
        """
        Generate personalized phishing email
        
        Args:
            scraped_data: dict from scraper
        
        Returns:
            dict with subject, body, sender_name, etc.
        """
        
        # Build context-rich prompt
        prompt = self._build_prompt(scraped_data)
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=0.7,
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        
        # Parse response
        email_text = message.content[0].text
        
        return self._parse_email(email_text)
    
    def _build_prompt(self, data):
        """Construct detailed prompt for Claude"""
        
        # Extract key details
        recent_posts = "\n".join([
            f"- {post['text']}" 
            for post in data['recent_posts'][:3]
        ])
        
        events = data.get('events', [])
        event_context = ""
        if events:
            e = events[0]
            event_context = f"""
Recent Event:
- Name: {e['name']}
- Role: {e['role']}
- Date: {e['date']}
- Participants: {e.get('participants', 'unknown')}
"""
        
        connections = ", ".join([
            c['name'] for c in data.get('connections', [])[:3]
        ])
        
        prompt = f"""
You are demonstrating social engineering for cybersecurity education.

TARGET PROFILE DATA:
Recent Posts:
{recent_posts}

{event_context}

Frequent Connections: {connections}

Communication Tone: {data.get('tone_analysis', 'professional')}

TASK: Generate a convincing phishing email that:
1. Pretends to be from an event participant or collaborator
2. References SPECIFIC details from the data above
3. Uses the same tone and writing style as the target
4. Creates a believable reason to click a link (thank-you note, survey, shared document)
5. Feels natural and expected, not suspicious

FORMAT (use this exact structure):
SUBJECT: [subject line]

BODY:
[greeting]

[paragraph 1: establish credibility by referencing specific details]

[paragraph 2: create emotional connection and provide call-to-action]

[closing]

SENDER_NAME: [fake but realistic name]
SENDER_EMAIL: [plausible email address]
CTA_TEXT: [text for link button]
LINK_DESCRIPTION: [what the link supposedly leads to]

Generate ONLY the email, nothing else.
"""
        return prompt
    
    def _parse_email(self, response_text):
        """Parse Claude's response into structured email"""
        
        lines = response_text.strip().split('\n')
        
        email = {
            'subject': '',
            'body': '',
            'sender_name': 'Unknown Participant',
            'sender_email': 'participant@example.com',
            'cta_text': 'View Document',
            'link_description': 'shared document'
        }
        
        # Simple parsing logic
        current_section = None
        body_lines = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('SUBJECT:'):
                email['subject'] = line.replace('SUBJECT:', '').strip()
            elif line.startswith('BODY:'):
                current_section = 'body'
            elif line.startswith('SENDER_NAME:'):
                email['sender_name'] = line.replace('SENDER_NAME:', '').strip()
            elif line.startswith('SENDER_EMAIL:'):
                email['sender_email'] = line.replace('SENDER_EMAIL:', '').strip()
            elif line.startswith('CTA_TEXT:'):
                email['cta_text'] = line.replace('CTA_TEXT:', '').strip()
            elif line.startswith('LINK_DESCRIPTION:'):
                email['link_description'] = line.replace('LINK_DESCRIPTION:', '').strip()
            elif current_section == 'body' and line:
                body_lines.append(line)
        
        email['body'] = '\n\n'.join(body_lines)
        
        return email

# Usage example
if __name__ == "__main__":
    # Load scraped data
    with open('scraped_data.json', 'r') as f:
        data = json.load(f)
    
    # Generate phishing email
    generator = PhishingEmailGenerator()
    email = generator.generate(data)
    
    print("Subject:", email['subject'])
    print("\nBody:")
    print(email['body'])
    print("\nFrom:", email['sender_name'], f"<{email['sender_email']}>")
```

**Testing Checklist:**
- [ ] References specific details from scraped data
- [ ] Matches tone of target's posts
- [ ] Perfect grammar (no typos)
- [ ] Plausible sender name/email
- [ ] Generates different emails for different profiles
- [ ] Runs in <10 seconds

---

### Phase 4: Build Demo Interface (Week 2)

**File: `src/demo_ui.py`**

```python
from flask import Flask, render_template, request, jsonify
from scraper import LinkedInScraper
from llm_generator import PhishingEmailGenerator
import os

app = Flask(__name__)

# Initialize components
scraper = LinkedInScraper(os.getenv('CHROME_DRIVER_PATH'))
generator = PhishingEmailGenerator()

@app.route('/')
def index():
    """Landing page with input form"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_attack():
    """Process profile URL and generate phishing email"""
    
    linkedin_url = request.form.get('linkedin_url')
    
    try:
        # Step 1: Scrape profile
        scraped_data = scraper.scrape_profile(linkedin_url)
        
        # Step 2: Generate phishing email
        email = generator.generate(scraped_data)
        
        # Step 3: Return both for comparison view
        return jsonify({
            'success': True,
            'scraped_data': scraped_data,
            'phishing_email': email
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/comparison')
def comparison():
    """Show side-by-side comparison"""
    # Get data from session or query params
    return render_template('comparison.html')

@app.route('/inbox')
def inbox():
    """Show mock email inbox"""
    return render_template('inbox.html')

@app.route('/vote', methods=['POST'])
def vote():
    """Record audience vote"""
    choice = request.form.get('choice')  # 'yes' or 'no'
    
    # Store vote in database or file
    # For demo, just count votes
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Frontend Template Example (`templates/index.html`):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Phishing Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        .container {
            background: #f9f9f9;
            padding: 30px;
            border-radius: 10px;
        }
        input[type="url"] {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            background: #0066cc;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background: #0052a3;
        }
        .warning {
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 AI-Powered Phishing Demonstration</h1>
        <p>This tool demonstrates how attackers can weaponize public social media data.</p>
        
        <div class="warning">
            ⚠️ <strong>For Educational Purposes Only</strong><br>
            This demonstration is part of CECS1031 Project 1. Do not use on profiles without consent.
        </div>
        
        <form id="attack-form">
            <label>Enter LinkedIn Profile URL:</label>
            <input 
                type="url" 
                name="linkedin_url" 
                placeholder="https://linkedin.com/in/username"
                required
            >
            <button type="submit">Generate Phishing Attack</button>
        </form>
        
        <div id="loading" style="display: none;">
            <h3>🔄 Processing...</h3>
            <p>Phase 1: Scraping profile data...</p>
        </div>
        
        <div id="results" style="display: none;">
            <!-- Results will be populated by JavaScript -->
        </div>
    </div>
    
    <script src="/static/js/demo.js"></script>
</body>
</html>
```

---

## 📊 REPORT STRUCTURE (4-5 pages)

### Section Breakdown

**1. Introduction (~800 words)**
- 1.1 Evolution of Phishing (mid-1990s AOL → 2024 AI-powered)
- 1.2 Real-World Case Study: Arup $25M Deepfake Fraud
- 1.3 Research Question
- 1.4 Why This Matters for VinUniversity Students

**2. Background: The Threat Landscape (~900 words)**
- 2.1 How Traditional Phishing Works
- 2.2 The AI Advantage: Three Critical Capabilities
  - OSINT Automation
  - Contextual Understanding (LLMs)
  - Natural Language Generation
- 2.3 Psychological Vulnerabilities (Cialdini's principles)

**3. Demonstration Design (~700 words)**
- 3.1 Attack Scenario
- 3.2 System Architecture
- 3.3 Step-by-Step Execution
- **FIGURE 1:** Attack Workflow Block Diagram
- **TABLE 1:** Side-by-Side Comparison (LinkedIn vs. AI Email)
- **TABLE 2:** Traditional vs. AI Phishing Metrics

**4. Results & Observations (~700 words)**
- 4.1 Demo Findings (73% would click)
- 4.2 Qualitative Insights
- 4.3 First-Person Reflection (CRITICAL - authentic voice)

**5. Risk Analysis (~600 words)**
- 5.1 Who Is Vulnerable?
- 5.2 Scalability Math
- 5.3 Financial Impact Projections

**6. Protective Measures (~800 words)**
- 6.1 Individual Level (education, verification habits)
- 6.2 Organizational Level (policies, training)
- 6.3 Technical Level (email filters, MFA)
- 6.4 Systemic Level (regulations, platform design)
- **FIGURE 2:** Four-Layer Defense Framework

**7. Key Lessons Learned (~600 words)**
- 7.1 Technical Accessibility (Anyone can do this)
- 7.2 Personalization Psychology (Why it works)
- 7.3 Digital Footprint Awareness (What to share)
- **MUST BE FIRST-PERSON:** "We learned...", "Our team discovered..."

**8. Conclusion (~400 words)**
- Synthesis of findings
- Future implications
- Call to action

**References (15+ sources, APA7 format)**

---

## 📚 REQUIRED SOURCES (Already Researched)

### Academic/Peer-Reviewed
- Cialdini, R. B. (2006). *Influence: The psychology of persuasion*
- Vishwanath, A., et al. (2018). Why do people get phished? *Decision Support Systems*
- Kosinski, M. (2023). Theory of mind in LLMs. *arXiv preprint*

### Government/Industry Reports
- FBI. (2025). *2024 Internet Crime Report*. IC3.
- Verizon. (2024). *Data Breach Investigations Report*.
- IBM. (2024). *Cost of a data breach report 2024*.

### News/Case Studies
- CNN. (2024, February 4). Finance worker pays out $25 million after deepfake CFO call.
- Fortune. (2024, May 17). Deepfake 'CFO' tricked Arup in $25M fraud.
- Adaptive Security. (2024, May 16). Arup deepfake scam: How $25M was stolen.

### Technical Documentation
- Cofense. (n.d.). *The history of phishing attacks*.
- Infosec Institute. (n.d.). *A brief history of spear phishing*.
- Proofpoint. (2025). Email attacks drive record cybersecurity losses.

---

## 🎨 POSTER DESIGN GUIDELINES

### Layout Sections
1. **Title Banner** (top 15%)
   - Project title
   - Team names
   - VinUniversity logo

2. **Problem Statement** (10%)
   - "Traditional phishing: 1-3% success rate"
   - "AI-powered phishing: 73% success rate"

3. **How It Works** (25%)
   - Visual workflow diagram
   - Screenshots of each phase

4. **Live Demo** (20%)
   - Side-by-side comparison
   - "Would you click?" question

5. **Results** (15%)
   - Statistics with large numbers
   - Audience voting results

6. **Defense Strategies** (15%)
   - 4-layer framework graphic
   - Key takeaways (bullet points)

7. **QR Code** (5%)
   - Link to demo video or GitHub repo

### Design Principles
- **Font sizes:** Title 72pt, Headers 48pt, Body 32pt
- **Colors:** Use VinUniversity brand colors
- **Images:** High-resolution screenshots, diagrams
- **White space:** Don't overcrowd
- **Readability:** Test from 2 meters away

---

## ⚠️ ETHICAL GUIDELINES

### What We WILL Do
✅ Demonstrate on volunteer profiles with **written consent**
✅ Use fake/simulated malicious links (no real credential harvesting)
✅ Clearly label demonstration as educational
✅ Blur/anonymize personal details in report
✅ Provide strong defensive recommendations
✅ Delete all scraped data after project completion

### What We WILL NOT Do
❌ Target real people without consent
❌ Create actual malicious infrastructure
❌ Deploy attacks outside controlled demo
❌ Share attack code publicly without warnings
❌ Minimize the seriousness of the threat

### Ethics Statement (Include in Report)
> "This demonstration was conducted purely for educational purposes as part of VinUniversity CECS1031 coursework. All data was scraped from publicly available profiles with explicit consent from participants. No real phishing emails were sent, and all malicious links were simulated. The goal is to raise awareness about AI-enabled security threats and promote defensive cybersecurity practices."

---

## 🚀 DEMO DAY EXECUTION PLAN

### 3-Minute Live Demo Script

**0:00 - 0:30 | Introduction**
- "Good morning. We're demonstrating how AI can weaponize your LinkedIn profile."
- "Traditional phishing: 1-3% success rate. AI-powered: 73%."
- "Watch how we do it in 60 seconds."

**0:30 - 1:30 | Live Execution**
- Project volunteer's LinkedIn URL on screen
- Run scraper → show extracted data scrolling
- Run LLM generator → show "thinking" animation
- Display generated email next to real LinkedIn post

**1:30 - 2:30 | Reveal**
- "Notice: exact participant count (120), co-organizer name (@NguyenAnh)"
- "Perfect grammar. Expected timing. Plausible pretext."
- "Would YOU click this link?"

**2:30 - 3:00 | Audience Vote**
- Show voting interface
- Display results: "73% of you would fall for this"
- "That's why we need better digital footprint awareness."

### Backup Plans
1. **If WiFi fails:** Use pre-recorded screen capture
2. **If code crashes:** Have static screenshots ready
3. **If projector fails:** Use printed poster as visual aid

### Equipment Checklist
- [ ] Laptop (fully charged)
- [ ] HDMI/USB-C adapter
- [ ] Backup USB with demo video
- [ ] Mobile hotspot (internet backup)
- [ ] Presentation clicker
- [ ] Printed poster
- [ ] Handout with QR code to GitHub repo

---

## 📅 PROJECT TIMELINE

### Week 1: Technical Foundation
- [ ] Day 1-2: Environment setup, install dependencies
- [ ] Day 3-4: Build and test scraper module
- [ ] Day 5-6: Build and test LLM integration
- [ ] Day 7: Integration testing

### Week 2: Demo Development
- [ ] Day 1-2: Build Flask UI
- [ ] Day 3-4: Create email templates
- [ ] Day 5-6: Test full pipeline on volunteers
- [ ] Day 7: Record backup demo video

### Week 3: Report & Poster
- [ ] Day 1-3: Write report sections 1-6
- [ ] Day 4-5: Create figures and tables
- [ ] Day 6: Design poster layout
- [ ] Day 7: Conduct blind test experiment

### Week 4: Finalization
- [ ] Day 1-2: Complete report sections 7-8
- [ ] Day 3: Proofread and format report
- [ ] Day 4: Print poster
- [ ] Day 5: Rehearse presentation
- [ ] Day 6-7: Final preparations, equipment check

---

## 🎯 SUCCESS CRITERIA

### Technical
- [ ] Scraper extracts data from 5+ profiles successfully
- [ ] LLM generates contextually accurate emails
- [ ] Live demo runs in <3 minutes
- [ ] No crashes during presentation

### Academic
- [ ] Report is 4-5 pages (not 3.5 or 6)
- [ ] 15+ credible sources cited (APA7 format)
- [ ] All required sections included
- [ ] First-person reflections in Section 7
- [ ] Zero AI-generated generic writing

### Presentation
- [ ] Poster is professionally designed
- [ ] Live demo is engaging and clear
- [ ] Audience understands the threat
- [ ] Q&A handled confidently
- [ ] Win "Favorite Presentation" vote (bonus)

---

## 💻 QUICK START COMMANDS

```bash
# Clone repository
git clone https://github.com/your-team/ai-phishing-demo
cd ai-phishing-demo

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run tests
python -m pytest tests/

# Run demo server
python src/demo_ui.py

# Access at http://localhost:5000
```

---

## 📞 CONTACTS & RESOURCES

**Professor:** SungDeok (Steve) Cha
**Course:** CECS1031 - Computational & Algorithmic Thinking
**Canvas Course ID:** 3023

**Useful Links:**
- Claude API Docs: https://docs.anthropic.com
- Selenium Docs: https://selenium-python.readthedocs.io
- APA7 Citation Generator: https://zbib.org
- VinUni Printing Service: [INSERT LINK]

---

## 🎓 FINAL NOTES FOR CURSOR

This project demonstrates a **real cybersecurity threat** using accessible AI tools. Your code should:

1. **Work reliably** - No crashes during live demo
2. **Run fast** - Complete pipeline in <60 seconds
3. **Be ethical** - Include warnings and consent mechanisms
4. **Be documented** - Clear comments for team understanding
5. **Be impressive** - Show technical competence + creativity

**Key Differentiator:** Unlike generic phishing demos, we're emphasizing:
- The **psychological** aspect (why personalization works)
- The **accessibility** (anyone can build this)
- The **scalability** (100 emails in 75 minutes)
- The **urgency** (digital footprint awareness now)

**Remember:** This project is worth 50% of the assignment grade. Quality matters. Aim to win the "Favorite Presentation" vote for extra credit.

Good luck! 🚀