# decroustra.AI — Missing Persons Monitoring Agent for Côte d'Ivoire

🕵️ **Track 3: Security & Compliance** — Web Data UNLOCKED Hackathon (Bright Data × lablab.ai)

*"Centralize alerts. Find people."*

---

## 🔴 Problem

In Côte d'Ivoire, missing person alerts are scattered across dozens of Facebook public groups, news sites, and forums.

A family searching for a loved one must:
- Monitor 5+ different Facebook groups
- Manually scan hundreds of posts daily
- Cross-reference information by hand
- Call 15+ different numbers

**Zero centralization exists.**

---

## 🟢 Solution

**decroustra.AI** is an AI agent that:

| Action | Detail |
|--------|--------|
| **Scrapes continuously** | Facebook public groups (with Google + news sites ready) |
| **Extracts automatically** | Name, age, location, date, contact from each post via DeepSeek |
| **Detects duplicates** | Same person reported 3 times = 1 alert (111 groups found) |
| **Matches Missing↔Found** | Cross-references "found!" posts with active missing alerts |
| **Natural language search** | *"Children missing in Yopougon?"* — *"My son David, 11, Abidjan?"* |

---

## ⚠️ Clear Limitations (shown on opening)

- **Does not replace emergency services** (Police 100 or 199 , Fire 110 / 111 / 170)
- **No legal or medical advice**
- **Public data only** — accuracy cannot be 100% guaranteed
- **Does not contact families directly**

---

## 🧱 Architecture

```
User → [Flask Chat Interface] → [DeepSeek] → Response
                    ↓
          [Search Engine]
                    ↓
          [alerts.json — 1,800+ alerts]
                    ↑
  ┌─────────────────┼───────────────────┐
  ↓                 ↓                   ↓
[Facebook Scraper] [SERP API]     [Web Unlocker]
(Bright Data)     (Google Search)  (News sites)
```

---

## 🔧 Tech Stack

| Technology | Usage |
|------------|-------|
| **Bright Data Web Unlocker** | Bypass Facebook blocking |
| **Bright Data Facebook Scraper API** | Structured JSON posts from groups |
| **Bright Data SERP API** | Multi-source Google search (ready) |
| **DeepSeek API** | Missing person extraction + Chatbot |
| **Python + Flask** | Web server + interface |
| **JSON** | Local storage (no database needed) |

---

## 📊 Results (real data from Ivorian Facebook groups)

| Metric | Value |
|--------|-------|
| Facebook posts scraped | 7,139 |
| Posts analyzed by DeepSeek | 3,951 |
| **Alerts extracted** | **1,872** |
| Duplicate groups detected | 111 |
| Locations covered | 949 |
| Age range | 2 — 90 years |

Source: "SOS ENFANTS DISPARUS DE COTE D'IVOIRE" and related public Facebook groups.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys (.env)
cp .env.example .env
# → Add BRIGHT_DATA_API_KEY, BRIGHT_DATA_ZONE, DEEPSEEK_API_KEY

# 3. Scrape data
python facebook_scraper.py    # Facebook structured posts
python web_scraper.py         # Google + news sites

# 4. Extract missing persons
python run_extraction.py      # DeepSeek analyzes all posts

# 5. Detect duplicates + match resolved cases
python dedup.py

# 6. Launch interface
python app.py
# → http://localhost:5000
```

---

## 📁 Project Structure

```
decroustra.AI/
├── app.py                  # Flask server + chat API
├── search.py               # Search engine (location, age, keyword, NLP)
├── scraper.py              # Web Unlocker (Facebook HTML)
├── facebook_scraper.py     # Facebook Scraper API (structured JSON)
├── web_scraper.py          # SERP API + news sites
├── run_extraction.py       # DeepSeek batch extraction
├── dedup.py                # Duplicate detection + Missing↔Found matching
├── config.py               # API keys
├── templates/
│   ├── index.html          # Chat interface
│   └── slide.html          # Presentation slide
├── data/
│   ├── alerts.json         # Alert database
│   └── raw/                # Raw scraped data
├── requirements.txt
├── .env.example
├── README.md
└── agent.md
```

---


## 🏆 Hackathon

- **Event:** Web Data UNLOCKED Hackathon (Bright Data × lablab.ai)
- **Track:** 🛡️ Security & Compliance
- **Dates:** May 25–30, 2026
- **Location:** Côte d'Ivoire (online) + San Francisco (onsite finale)
- **Repository:** [github.com/gedenedavid-ops/decroustra-AI](https://github.com/gedenedavid-ops/decroustra-AI)

---

**decroustra.AI** — Because centralized information saves lives.
