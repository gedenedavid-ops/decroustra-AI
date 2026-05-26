# decroustra.AI — Agent de surveillance des disparitions en Côte d'Ivoire

🕵️ **Track 3 : Security & Compliance** — Web Data UNLOCKED Hackathon (Bright Data)

*"Centralisons les alertes. Retrouvons les personnes."*

---

## 🔴 Problème

En Côte d'Ivoire, les annonces de disparition sont éparpillées sur les réseaux sociaux : groupes Facebook publics, pages d'actualité, forums. 

Une famille qui cherche un proche doit :
- Surveiller 5+ groupes Facebook différents
- Scanner des centaines de posts par jour
- Recouper les informations manuellement
- Appeler 15 numéros différents

**Aucune centralisation n'existe.**

---

## 🟢 Solution

**decroustra.AI** est un agent IA qui :

| Action | Détail |
|--------|--------|
| **Scrape en continu** | Groupes Facebook publics, Google Actualités, sites d'actus ivoiriens |
| **Extrait automatiquement** | Nom, âge, lieu, date, contact de chaque disparition |
| **Détecte les doublons** | Une même personne signalée 3 fois = 1 alerte |
| **Apparie Disparu/Retrouvé** | Croise les posts "retrouvé !" avec les avis de recherche |
| **Permet de rechercher** | Chat en langage naturel : *"enfants disparus à Yopougon ?"* |

---

## ⚠️ Limites claires (affichées dès l'ouverture)

- **Ne remplace pas les secours** (Police 170, Pompiers 185)
- **Ne donne pas de conseils** juridiques ou médicaux
- **Données publiques uniquement** — non vérifiées à 100%
- **Ne contacte pas les familles** directement

---

## 🧱 Architecture

```
Utilisateur → [Interface Chat Flask] → [DeepSeek] → Réponse
                        ↓
              [Moteur de recherche]
                        ↓
              [alerts.json — 1800+ alertes]
                        ↑
    ┌───────────────────┼───────────────────┐
    ↓                   ↓                   ↓
[Facebook Scraper]  [SERP API]     [Web Unlocker]
(Bright Data)      (Google Search)  (Sites d'actus)
```

---

## 🔧 Stack technique

| Technologie | Usage |
|-------------|-------|
| **Bright Data Web Unlocker** | Contourner les blocages Facebook |
| **Bright Data Facebook Scraper API** | Posts structurés des groupes |
| **Bright Data SERP API** | Recherche Google multi-sources |
| **DeepSeek API** | Extraction des disparitions + Chatbot |
| **Python + Flask** | Serveur web + interface |
| **JSON** | Stockage local (pas de BDD) |

---

## 📊 Résultats (données réelles)

| Métrique | Valeur |
|----------|--------|
| Posts Facebook scrappés | 7 139 |
| Posts analysés | 3 951 |
| **Alertes extraites** | **1 872** |
| Groupes de doublons | 111 |
| Localités couvertes | 949 |
| Âge min / max | 2 ans / 90 ans |

---

## 🚀 Lancement

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer les clés API (.env)
cp .env.example .env
# → Ajouter BRIGHT_DATA_API_KEY, BRIGHT_DATA_ZONE, DEEPSEEK_API_KEY

# 3. Scraper les données
python facebook_scraper.py    # Posts Facebook structurés
python web_scraper.py         # Google + sites d'actus

# 4. Extraire les disparitions
python run_extraction.py      # DeepSeek analyse tous les posts

# 5. Détecter doublons + appariements
python dedup.py

# 6. Lancer l'interface
python app.py
# → http://localhost:5000
```

---

## 📁 Structure

```
decroustra.AI/
├── app.py                  # Serveur Flask + API chat
├── search.py               # Moteur de recherche
├── scraper.py              # Web Unlocker (Facebook HTML)
├── facebook_scraper.py     # Facebook Scraper API (JSON structuré)
├── web_scraper.py          # SERP API + sites d'actus
├── run_extraction.py       # DeepSeek extraction massive
├── dedup.py                # Détection doublons + appariements
├── config.py               # Clés API
├── templates/
│   └── index.html          # Interface chat
├── data/
│   ├── alerts.json         # Base d'alertes
│   └── raw/                # Données brutes
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🎥 Demo vidéo (YouTube)

[Lien vers la vidéo de démonstration — 2 minutes]

---

## 🏆 Hackathon

- **Événement :** Web Data UNLOCKED Hackathon (Bright Data × lablab.ai)
- **Track :** 🛡️ Security & Compliance
- **Période :** 26-30 Mai 2026
- **Lieu :** Côte d'Ivoire (online) + San Francisco (onsite finale)

---

**decroustra.AI** — Parce que l'information centralisée sauve des vies.
