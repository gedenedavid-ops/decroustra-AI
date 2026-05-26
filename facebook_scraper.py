"""
facebook_scraper.py — Scraping des groupes Facebook via l'API Bright Data Facebook Scraper

Utilise l'API dédiée Facebook Posts by Group de Bright Data
pour récupérer les posts structurés en JSON.

Documentation : https://docs.brightdata.com/api-reference/scrapers/social-media-apis/facebook-posts-by-group-collect-by-url
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

from config import BRIGHT_DATA_API_KEY, validate_config

# ─── Configuration ───────────────────────────────────────────────────────────

FACEBOOK_API_URL = "https://api.brightdata.com/datasets/v3/scrape"
PROGRESS_URL = "https://api.brightdata.com/datasets/v3/progress"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot"
DATASET_ID = "gd_lz11l67o2cb3r0lkj3"  # Facebook Posts by Group

GROUP_CANDIDATES = [
    {
        "url": "https://www.facebook.com/groups/3153156638063292",
        "name": "SOS-AVIS DE DISPARITION",
    },
    {"url": "https://www.facebook.com/groups/630419480441627", "name": "Groupe 2"},
    {"url": "https://www.facebook.com/groups/821910354606692", "name": "Groupe 3"},
    {"url": "https://www.facebook.com/groups/327563508313339", "name": "Groupe 4"},
]

RAW_DIR = "data/raw"
DATA_DIR = "data"
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")


# ─── Fonctions ───────────────────────────────────────────────────────────────


def get_headers():
    return {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }


def fetch_group_posts(group_url: str) -> list | None:
    """
    Récupère les posts d'un groupe Facebook public via l'API Bright Data.
    Gère le mode asynchrone (polling du snapshot).
    """
    if not BRIGHT_DATA_API_KEY:
        print("❌ BRIGHT_DATA_API_KEY manquante.")
        return None

    print(f"\n🌐 Récupération des posts de : {group_url}")

    headers = get_headers()
    params = {"dataset_id": DATASET_ID, "include_errors": "true"}
    payload = {"input": [{"url": group_url}]}

    try:
        response = requests.post(
            FACEBOOK_API_URL,
            params=params,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            posts = response.json()
            print(f"✅ {len(posts)} posts récupérés (mode synchrone)")
            return posts

        elif response.status_code == 202:
            # Mode asynchrone — on doit poller
            data = response.json()
            snapshot_id = data.get("snapshot_id")
            if not snapshot_id:
                print(f"❌ Pas de snapshot_id dans la réponse: {data}")
                return None
            print(f"⏳ Requête asynchrone acceptée. Snapshot ID: {snapshot_id}")
            return poll_snapshot(snapshot_id, headers)

        elif response.status_code == 400:
            error = response.text[:300]
            if "not active" in error:
                print("⚠️  Compte non actif pour ce produit.")
                print("   Utilise le Web Unlocker à la place (python scraper.py)")
            else:
                print(f"❌ Erreur 400: {error}")
            return None
        else:
            print(f"❌ Erreur {response.status_code}: {response.text[:300]}")
            return None

    except requests.exceptions.Timeout:
        print("❌ Timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        return None


def poll_snapshot(snapshot_id: str, headers: dict, max_wait: int = 120) -> list | None:
    """Poule le statut d'un snapshot jusqu'à ce qu'il soit prêt"""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = requests.get(
                f"{PROGRESS_URL}/{snapshot_id}",
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                status = resp.json()
                state = status.get("status", "")
                print(f"   Statut: {state}")

                if state == "ready":
                    print("   Téléchargement du snapshot...")
                    return download_snapshot(snapshot_id, headers)
                elif state in ("failed", "error"):
                    print(f"❌ Snapshot échoué: {status}")
                    return None

            time.sleep(5)
        except Exception as e:
            print(f"❌ Erreur polling: {e}")
            return None

    print("❌ Timeout d'attente du snapshot")
    return None


def download_snapshot(snapshot_id: str, headers: dict) -> list | None:
    """Télécharge les résultats d'un snapshot"""
    try:
        resp = requests.get(
            f"{SNAPSHOT_URL}/{snapshot_id}",
            headers=headers,
            timeout=60,
        )
        if resp.status_code == 200:
            posts = resp.json()
            print(f"✅ {len(posts)} posts récupérés")
            return posts
        else:
            print(f"❌ Erreur téléchargement: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur téléchargement: {e}")
        return None


def save_posts(posts: list, group_url: str) -> str | None:
    """Sauvegarde les posts JSON dans data/raw/"""
    os.makedirs(RAW_DIR, exist_ok=True)
    group_id = group_url.rstrip("/").split("/")[-1]
    filename = f"fb_api_{group_id}.json"
    filepath = os.path.join(RAW_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"💾 Sauvegardé dans : {filepath}")
    return filepath


def posts_to_alerts(posts: list, group_url: str) -> list:
    """Convertit les posts Facebook en format alerte structurée."""
    alerts = []
    for i, post in enumerate(posts):
        content = post.get("content") or ""
        post_id = post.get("post_id", f"unknown_{i}")
        timestamp = datetime.now(timezone.utc)

        alert = {
            "id": f"fb_{post_id}",
            "post_type": post.get("post_type", "Post"),
            "content": content[:1000] if content else "",
            "author": post.get("user_username_raw", "Inconnu"),
            "date_posted": post.get("date_posted", ""),
            "post_url": post.get("url", ""),
            "source_group": group_url,
            "status": "pending",
            "scraped_at": timestamp.isoformat(),
        }
        alerts.append(alert)
    return alerts


def save_alerts_json(alerts: list):
    """Sauvegarde les alertes dans data/alerts.json"""
    os.makedirs(DATA_DIR, exist_ok=True)

    existing = []
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            existing_data = json.load(f)
            existing = existing_data.get("alerts", [])

    all_alerts = existing + alerts
    seen = set()
    unique = []
    for a in all_alerts:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique.append(a)

    data = {
        "total_alerts": len(unique),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "alerts": unique,
    }

    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 {len(unique)} posts dans {ALERTS_FILE}")
    return unique


# ─── Pipeline ────────────────────────────────────────────────────────────────


def run():
    if not validate_config():
        sys.exit(1)

    print("=" * 60)
    print("📘 Facebook Scraper API — Posts des groupes")
    print("=" * 60)

    all_posts = []
    total_alerts = []

    for group in GROUP_CANDIDATES:
        url = group["url"]
        name = group["name"]
        print(f"\n{'=' * 40}\n📌 {name}")

        posts = fetch_group_posts(url)
        if posts is None:
            continue

        filepath = save_posts(posts, url)
        if filepath:
            with_content = [p for p in posts if p.get("content")]
            print(f"   📝 {len(with_content)} posts avec texte")

        all_posts.extend(posts)
        total_alerts.extend(posts_to_alerts(posts, url))

    if total_alerts:
        save_alerts_json(total_alerts)

    print("\n" + "=" * 60)
    print("📊 Résumé")
    print("=" * 60)
    print(f"   Groupes : {len(GROUP_CANDIDATES)}")
    print(f"   Posts : {len(all_posts)}")
    print(f"   En base : {len(total_alerts)}")
    print("=" * 60)


if __name__ == "__main__":
    run()
