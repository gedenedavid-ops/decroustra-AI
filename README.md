# decroustra.AI — Missing Persons Monitoring Agent for Cote d'Ivoire

> *Dedie a mon pere. 28 mai 2026.*

---

**Track 3: Security & Compliance** — Web Data UNLOCKED Hackathon (Bright Data x lablab.ai)

*"Centralize alerts. Find people."*

---

## Problem

In Cote d'Ivoire, missing person alerts are scattered across dozens of Facebook public groups, news sites, and forums.

A family searching for a loved one must:
- Monitor 5+ different Facebook groups
- Manually scan hundreds of posts daily
- Cross-reference information by hand
- Call 15+ different numbers

**Zero centralization exists.**

---

## Solution

**decroustra.AI** is an AI agent that:

| Action | Detail |
|--------|--------|
| **Scrapes continuously** | Facebook public groups (CI, BF, Mali, Senegal) |
| **Extracts automatically** | Name, age, location, date, contact via DeepSeek |
| **Detects duplicates** | Same person reported 3 times = 1 alert |
| **Matches Missing-Found** | Cross-references found posts with active missing alerts |
| **Natural language search** | *"Children missing in Yopougon?"* |

---

## Limitations

- Does not replace emergency services
- No legal or medical advice
- Public data only

---

## Architecture

```
React (Vite)  ->  Flask API  ->  DeepSeek
                    |
              Search Engine
                    |
            alerts.json (1,800+ alerts)
                    |
    Facebook Scraper  +  SERP API  +  Web Unlocker
       (Bright Data)     (Google)     (News sites)
```

---

## Tech Stack

| Technology | Usage |
|------------|-------|
| **Bright Data** | Facebook Scraper, SERP API, Web Unlocker |
| **DeepSeek API** | Missing person extraction + Chatbot |
| **Python + Flask** | Backend API |
| **React + Vite + TypeScript** | Frontend |
| **Tailwind CSS** | Styling |
| **JSON** | Local storage |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys (.env)
cp .env.example .env
# -> Add BRIGHT_DATA_API_KEY, BRIGHT_DATA_ZONE, DEEPSEEK_API_KEY

# 3. Scrape data
python orchestrator.py

# 4. Launch backend
python app.py

# 5. Launch frontend (separate terminal)
cd frontend && npm install && npm run dev
# -> http://localhost:5173
```

---

## Hackathon

- **Event:** Web Data UNLOCKED Hackathon (Bright Data x lablab.ai)
- **Track:** Security & Compliance
- **Dates:** May 25-30, 2026
- **Repository:** [github.com/gedenedavid-ops/decroustra-AI](https://github.com/gedenedavid-ops/decroustra-AI)

---

**decroustra.AI** — Because centralized information saves lives.
