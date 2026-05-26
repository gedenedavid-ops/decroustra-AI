decoustra.ia - Hackathon Project

## 📌 IDENTITÉ DU PROJET

**Nom:** decoustra.ia - Agent de surveillance des disparitions en Côte d'Ivoire

**Hackathon:** Web Data UNLOCKED Hackathon (Bright Data)

**Track:** 🛡️ Track 3 - Security & Compliance

**Tagline:** *"Centralisons les alertes. Retrouvons les personnes."*

## 👥 PERSONNES IMPLIQUÉES

- **MOI** (développeur humain) - Côte d'Ivoire
- **TOI** (l'IA qui lit ce fichier) - Tu m'aides à coder
- **DeepSeek API** - Le modèle qui analyse et génère les réponses

## 🎯 OBJECTIF

Construire un agent IA qui :
1. **Scrape en continu** les groupes Facebook publics sur les disparitions en CI
2. **Extrait automatiquement** les infos clés (nom, âge, lieu, date, contact)
3. **Permet aux utilisateurs de poser des questions** via chat :
   - "Y'a-t-il une disparition à Yopougon ?"
   - "Montre-moi les enfants disparus cette semaine"
   - "Résumé des alertes des dernières 24h"

## 🔧 TECHNOLOGIES

| Technologie | Usage | Pourquoi |
|-------------|-------|----------|
| Bright Data Web Unlocker | Scraper Facebook (groupes publics) | Facebook bloque les scraper normaux |
| Bright Data MCP Server | Interaction IA-native avec le web | Plus simple que d'appeler l'API brute |
| DeepSeek API | Extraction des infos + chatbot | J'ai des crédits |
| Python | Langage principal | Rapide, simple |
| Flask | Serveur web pour l'interface | Démo facile |
| JSON | Stockage local | Pas besoin de base de données |

## 📁 STRUCTURE DES FICHIERS
alerte-ci/
│
├── AGENT.md # Ce fichier
├── roadmap.md # Plan jour par jour
│
├── config.py # Clés API
├── scraper.py # Scraping avec Bright Data
├── extractor.py # DeepSeek extrait les infos des disparitions
├── search.py # Recherche dans les alertes
├── app.py # Serveur Flask + interface chat
│
├── data/
│ ├── raw/ # Données brutes scrappées
│ ├── alerts.json # Toutes les alertes structurées
│ └── resolved.json # Alertes résolues (retrouvailles)
│
├── templates/
│ └── index.html # Interface chat
│
└── requirements.txt

text

## 📅 ROADMAP RAPIDE

| Jour | Objectif |
|------|----------|
| J1 | Setup Bright Data + scraper 1 groupe Facebook public |
| J2 | DeepSeek extrait nom/âge/lieu/date/contact → JSON |
| J3 | Recherche + détection des doublons |
| J4 | Interface chat + question/réponse |
| J5 | Vidéo + soumission |

## 🔑 CLÉS API

```python
# config.py
BRIGHT_DATA_API_KEY = "ton_api_key"
DEEPSEEK_API_KEY = "ton_api_key_deepseek"
📦 DÉPENDANCES
text
requests
flask
openai
python-dotenv
🎤 PITCH POUR LE JURY
Problème: En Côte d'Ivoire, les annonces de disparition sont éparpillées sur Facebook, sans centralisation. Les familles perdent un temps précieux.

Solution: decoustra.ia - Un agent IA qui scrappe, structure et surveille toutes les alertes en temps réel.

Bright Data: Web Unlocker pour accéder aux groupes Facebook publics (bloqués aux scraper classiques).

Track 3: Sécurité des personnes - L'information est une question de sécurité citoyenne.

Impact: Centraliser l'information = retrouver plus vite.

✅ CRITÈRES DE SUCCÈS
Au moins 1 groupe Facebook scrappé avec succès

Au moins 5 alertes extraites en JSON

Interface chat qui répond aux questions

Vidéo de démo soumise

🚨 PIÈGES À ÉVITER
Ne PAS scraper les groupes privés → Reste sur les groupes publics

Ne PAS stocker de photos → Garde seulement les liens

Ne PAS donner de conseils → Tu centralises, tu ne juges pas

Respecter les familles → Ton code aide, ne nuit pas

Signé: decoustra.ia
