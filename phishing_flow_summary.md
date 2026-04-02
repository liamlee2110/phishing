# AI Phishing Framework: End-to-End Flow Summary

This document provides a detailed overview of the automated spear-phishing pipeline, demonstrating how social media data is weaponized using Large Language Models (LLMs) for hyper-personalized social engineering attacks.

---

## 1. Information Gathering (Automated Scraper)
The process begins with harvesting publicly available (or semi-private) information from a target's Facebook profile.

*   **Technology**: Python + Playwright (Headless Chromium).
*   **Authentication**: Uses session cookies (via `Cookie-Editor` JSON imports) to bypass login walls and navigate as an authenticated friend of the target.
*   **Data Extraction Engine**: 
    *   **Recent Activity**: Scrapes the last 10+ posts to identify interests, writing style, and recent life events.
    *   **Social Graph Mapping**: Heuristically extracts "Frequent Connections" by looking for name mentions in patterns like *"with [Name]"*, *"thanks to [Name]"*, or direct mentions.
    *   **Contextual Events**: Identifies specific conferences, hackathons, or workshops the user attended (e.g., *"VinUni AI Workshop"*).
    *   **Linguistic Tone Analysis**: A heuristic engine that analyzes word choice, sentiment, and punctuation (e.g., "enthusiastic," "casual," "professional," "emoji-heavy") to build a stylometric profile.

---

## 2. Intelligence Analysis & Orchestration (LLM)
Once the raw data is captured, it is processed by a "Social Engineering Orchestrator" powered by **GPT-4o Mini**.

*   **Role-Play Prompting**: The LLM is instructed to act as a sophisticated social engineer demonstrating tactics for educational purposes.
*   **Deep-Knowledge Injection**: The model is fed the specific details from the scraper (posts, friendships, events).
*   **Tactical Objectives**:
    1.  **Impersonation**: Select a believable sender identity (e.g., a Vietnamese name like *Nguyen Minh Tuan*) likely to be in the target's network.
    2.  **Credibility (The Hook)**: Reference specific deep-knowledge from a previous post (e.g., *"I saw your post about the AI competition last week..."*) to instantly build trust.
    3.  **Tone Mimicry**: Match the target's captured formality and emoji usage.
    4.  **Call to Action (CTA)**: Create a plausible, non-generic reason to click (e.g., *"Shared the presentation photos here"* or *"Requesting feedback on this doc"*).

---

## 3. Payload Construction & Delivery
The framework generates a complete phishing artifact ready for delivery.

*   **Phishing Email Composition**:
    *   **Subject Line**: Context-aware and urgent (e.g., *"Photos from the VinUni event"*).
    *   **Personalization**: Uses real greetings and body text that flows naturally.
    *   **Sender Spoofing**: Generates a plausible fake email address matching the sender's identity.
*   **Delivery Mechanism**:
    *   **Dashboard Preview**: The attacker reviews the side-by-side comparison of "Scraped Data" vs "Generated Phishing Email."
    *   **Real Inbox Injection**: (Optional) Uses a **Google Apps Script** relay to send the generated email via the Gmail API to a real inbox for a physical demonstration.

---

## 4. Exploitation (The Landing Page)
The final stage of the flow is the user interaction with the phishing link.

*   **The "Trap"**: The email includes a button/link (CTA) leading to a controlled URL.
*   **Educational Payload**: Upon clicking, the user is redirected to the `/scam` page.
*   **The Reveal**: Instead of a credential harvester, the user sees a stark high-impact "You are scammed!" warning. 
*   **Educational Objective**: The page explains that in a real attack, their credentials or sensitive data would have been compromised, serving as a powerful "Aha!" moment for cybersecurity awareness.

---

## Summary of the "Weaponization" Chain
| Stage | Source | Process | Output |
| :--- | :--- | :--- | :--- |
| **Profilng** | Facebook | Scraper (Playwright) | Social Interests, Tone, Connections |
| **Synthesis** | LLM | Contextual Intelligence | Spear-Phishing Strategy |
| **Payload** | LLM Context | Generation | Hyper-personalized Email |
| **Attack** | Gmail/Web | Delivery | Click-through on Link |
| **Awareness** | Next.js | Educational Landing | Behavioral Correction |

---

> [!IMPORTANT]
> This framework is designed strictly for **CECS1031 — VinUniversity** educational purposes and authorized security awareness demonstrations.
