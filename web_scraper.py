"""
web_scraper.py — Scraping multi-sources avec Bright Data

Utilise le SERP API + Web Scraper API de Bright Data pour
collecter des alertes de disparition depuis plusieurs sources.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

from config import BRIGHT_DATA_API_KEY, BRIGHT_DATA_ZONE, SOURCES, validate_config

# ─── Configuration ───────────────────────────────────────────────────────────

RAW_DIR = "data/raw"
DATA_DIR = "data"
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")

# Reconstruction dynamique des queries et sites par pays
SEARCH_QUERIES = []
NEWS_SITES = []
for country, data in SOURCES.items():
    for site in data["news_sites"]:
        NEWS_SITES.append(f"https://www.{site}/search/?q=disparition")
    # Générer des requêtes Google localisées
    if country == "CI":
        SEARCH_QUERIES.extend(
            [
                "avis de disparition côte d'ivoire",
                "alerte disparition enfant abidjan",
            ]
        )
    elif country == "BF":
        SEARCH_QUERIES.extend(
            [
                "avis de disparition burkina faso",
                "alerte disparition ouagadougou",
            ]
        )
    elif country == "ML":
        SEARCH_QUERIES.extend(
            [
                "avis de disparition mali",
                "alerte disparition bamako",
            ]
        )
    elif country == "SN":
        SEARCH_QUERIES.extend(
            [
                "avis de disparition sénégal",
                "alerte disparition dakar",
            ]
        )


def get_headers():
    return {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }


# ─── SERP API (Google Search) ────────────────────────────────────────────────


def search_web(query: str, num_results: int = 10) -> list:
    """
    Cherche des alertes de disparition sur le web via Bright Data SERP API.

    Documentation: https://docs.brightdata.com/scraping-automation/serp-api
    """
    print(f'\n🌐 Recherche web: "{query}"')

    headers = get_headers()
    params = {
        "url": f"https://www.google.com/search?q={query}&num={num_results}&hl=fr",
        "format": "json",
        "zone": os.getenv("BRIGHT_DATA_ZONE", ""),
    }

    try:
        resp = requests.post(
            "https://api.brightdata.com/request",
            json=params,
            headers=headers,
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()
            results = []

            # Extraire les résultats de recherche
            organic = data.get("organic", []) if isinstance(data, dict) else []
            for r in organic:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("snippet", ""),
                        "source": "google_search",
                        "query": query,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

            print(f"   ✅ {len(results)} résultats trouvés")
            return results
        else:
            print(f"   ❌ Erreur {resp.status_code}")
            return []

    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []


# ─── Web Scraper API (sites d'actus) ────────────────────────────────────────


def scrape_news_site(url: str) -> list:
    """
    Scrape un site d'actualité via Bright Data Web Unlocker.
    """
    print(f"\n📰 Scraping: {url}")

    headers = get_headers()
    payload = {
        "zone": os.getenv("BRIGHT_DATA_ZONE", ""),
        "url": url,
        "format": "raw",
    }

    try:
        resp = requests.post(
            "https://api.brightdata.com/request",
            json=payload,
            headers=headers,
            timeout=60,
        )

        if resp.status_code == 200:
            import re

            html = resp.text

            # Extraction simple : titres et extraits
            results = []
            # Chercher les balises de titre
            titles = re.findall(r"<h[2-3][^>]*>(.*?)</h[2-3]>", html, re.DOTALL)
            for t in titles[:10]:
                clean = re.sub(r"<[^>]+>", "", t).strip()
                if clean and len(clean) > 20:
                    results.append(
                        {
                            "title": clean,
                            "url": url,
                            "snippet": clean[:200],
                            "source": "news_site",
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            print(f"   ✅ {len(results)} articles trouvés")
            return results
        else:
            print(f"   ❌ Erreur {resp.status_code}")
            return []

    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []


# ─── Agrégation ──────────────────────────────────────────────────────────────


def save_results(all_results: list):
    """Sauvegarde tous les résultats dans alerts.json"""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Charger les alertes existantes
    existing = []
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing = data.get("alerts", [])
            print(f"\n📂 {len(existing)} alertes existantes chargées")

    # Convertir les résultats en format alerte
    new_alerts = []
    for r in all_results:
        alert = {
            "id": f"web_{abs(hash(r.get('url', r.get('title', '')))) % 10**10}",
            "name": None,
            "age": None,
            "gender": None,
            "last_location": None,
            "disappearance_date": None,
            "contact": None,
            "source": r.get("source", "web"),
            "source_url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "status": "pending",
            "scraped_at": r.get("scraped_at", datetime.now(timezone.utc).isoformat()),
        }
        new_alerts.append(alert)

    # Fusion + déduplication
    seen_urls = {a.get("source_url", "") for a in existing if a.get("source_url")}
    unique_new = [a for a in new_alerts if a.get("source_url", "") not in seen_urls]

    combined = existing + unique_new

    output = {
        "total_alerts": len(combined),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "alerts": combined,
    }

    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Total: {len(combined)} alertes ({len(unique_new)} nouvelles)")
    return combined


# ─── Pipeline ────────────────────────────────────────────────────────────────


def run():
    if not validate_config():
        sys.exit(1)

    print("=" * 60)
    print("🌍 Scraping multi-sources Bright Data")
    print("=" * 60)

    all_results = []

    # 1. SERP API — Recherche web
    print("\n" + "─" * 40)
    print("📌 PHASE 1: Recherche Google (SERP API)")
    print("─" * 40)

    for query in SEARCH_QUERIES[:3]:  # Limiter à 3 requêtes pour commencer
        results = search_web(query)
        all_results.extend(results)
        time.sleep(1)  # Petite pause entre les requêtes

    # 2. Sites d'actualité
    print("\n" + "─" * 40)
    print("📌 PHASE 2: Sites d'actualité")
    print("─" * 40)

    for url in NEWS_SITES[:2]:
        results = scrape_news_site(url)
        all_results.extend(results)
        time.sleep(1)

    # 3. Sauvegarde
    if all_results:
        save_results(all_results)

    print("\n" + "=" * 60)
    print(f"✅ Terminé: {len(all_results)} nouveaux résultats")
    print("=" * 60)


# ─── Script de scraping continu (cron) ──────────────────────────────────────


def run_continuous(interval_minutes: int = 60):
    """
    Lance le scraping en continu toutes les X minutes.
    Utile pour un déploiement sur Render / Railway.
    """
    print(f"🔄 Scraping continu toutes les {interval_minutes} min")
    while True:
        run()
        print(f"\n⏳ Prochain scraping dans {interval_minutes} min...")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--continuous", type=int, help="Intervalle en minutes")
    parser.add_argument("--queries", type=int, default=3, help="Nombre de requêtes")
    args = parser.parse_args()

    if args.continuous:
        run_continuous(args.continuous)
    else:
        run()
