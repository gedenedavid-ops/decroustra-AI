"""
scraper.py — Scraping de groupes Facebook publics avec Bright Data Web Unlocker

Utilise l'API Bright Data Web Unlocker (https://api.brightdata.com/request)
pour contourner les blocages de Facebook et récupérer le contenu des groupes publics.

Documentation : https://docs.brightdata.com/scraping-automation/web-unlocker/send-your-first-request
"""

import json
import os
import sys
from datetime import datetime

import requests

from config import BRIGHT_DATA_API_KEY, BRIGHT_DATA_ZONE, validate_config

# ─── Configuration ───────────────────────────────────────────────────────────

# Groupes Facebook publics cibles
GROUP_CANDIDATES = [
    "https://www.facebook.com/groups/3153156638063292",
    "https://www.facebook.com/groups/630419480441627",
    "https://www.facebook.com/groups/821910354606692",
    "https://www.facebook.com/groups/327563508313339",
]

# Dossier de sauvegarde
RAW_DIR = "data/raw"

# Endpoint Bright Data (Direct API access)
BRIGHT_DATA_API_URL = "https://api.brightdata.com/request"


# ─── Fonctions ───────────────────────────────────────────────────────────────


def scrape_facebook_group(group_url: str) -> str | None:
    """
    Scrape les posts récents d'un groupe Facebook public via Bright Data.

    Utilise l'API REST directe de Bright Data :
    POST https://api.brightdata.com/request
    Authorization: Bearer {API_KEY}

    Args:
        group_url: URL complète du groupe Facebook (doit être PUBLIC)

    Returns:
        HTML brut de la page, ou None si erreur
    """
    if not BRIGHT_DATA_API_KEY:
        print("❌ BRIGHT_DATA_API_KEY manquante. Configure .env d'abord.")
        return None

    print(f"🌐 Scraping de : {group_url}")

    # La zone Bright Data est obligatoire pour l'API directe
    if not BRIGHT_DATA_ZONE:
        print("❌ BRIGHT_DATA_ZONE manquante dans .env")
        print("   Ajoute BRIGHT_DATA_ZONE=nom_de_ta_zone (ex: sco_ai)")
        return None

    # Payload JSON pour l'API Bright Data
    # Doc : https://docs.brightdata.com/scraping-automation/web-unlocker/send-your-first-request
    payload = {
        "zone": BRIGHT_DATA_ZONE,
        "url": group_url,
        "format": "raw",
    }

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            BRIGHT_DATA_API_URL,
            json=payload,
            headers=headers,
            timeout=120,  # 2 minutes max, Facebook est lent
        )

        if response.status_code == 200:
            print(f"✅ Succès ! {len(response.text)} caractères récupérés.")
            return response.text
        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"   Détail: {response.text[:500]}")
            return None

    except requests.exceptions.Timeout:
        print("❌ Timeout : le serveur n'a pas répondu à temps.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        return None


def save_raw_html(html: str, group_url: str) -> str | None:
    """
    Sauvegarde le HTML brut dans data/raw/ avec un horodatage.

    Returns:
        Chemin du fichier sauvegardé, ou None si erreur
    """
    os.makedirs(RAW_DIR, exist_ok=True)

    # Générer un nom de fichier lisible
    group_name = group_url.rstrip("/").split("/")[-1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{group_name}_{timestamp}.html"
    filepath = os.path.join(RAW_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"💾 Sauvegardé dans : {filepath}")
        return filepath
    except IOError as e:
        print(f"❌ Erreur d'écriture : {e}")
        return None


def extract_text_from_html(html: str) -> str:
    """
    Extrait le texte pertinent du HTML Facebook.
    Facebook charge le contenu dans des blobs JSON internes.
    On va chercher les textes lisibles (messages, commentaires).
    """
    import json
    import re

    texts = []

    # 1. Chercher les contenus JSON dans les balises <script type="application/json">
    #    Facebook stocke les posts dans ces blobs
    for match in re.finditer(
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL
    ):
        try:
            data = json.loads(match.group(1))
            # Parcourir récursivement pour trouver du texte
            stack = [data]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    for val in item.values():
                        stack.append(val)
                elif isinstance(item, list):
                    for val in item:
                        stack.append(val)
                elif isinstance(item, str) and len(item) > 30:
                    # Texte long = probablement un message
                    texts.append(item.strip())
        except (json.JSONDecodeError, TypeError):
            pass

    # 2. Extraction HTML classique pour le reste
    # Supprime les balises HTML
    html_text = re.sub(r"<[^>]+>", " ", html)
    # Supprime les espaces multiples
    html_text = re.sub(r"\s+", " ", html_text)

    # Ajouter les lignes de texte significatives
    for line in html_text.split("\n"):
        line = line.strip()
        if len(line) > 50 and not line.startswith("{") and not line.startswith("["):
            texts.append(line)

    # Déduplication et tri
    seen = set()
    unique = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return "\n\n".join(unique[:200])  # Limiter à 200 blocs de texte


def scrape_and_save(group_url: str) -> dict:
    """
    Pipeline complet : scrape → sauvegarde → retourne les métadonnées.
    """
    html = scrape_facebook_group(group_url)
    if not html:
        return {"success": False, "url": group_url, "error": "Scraping échoué"}

    filepath = save_raw_html(html, group_url)
    if not filepath:
        return {"success": False, "url": group_url, "error": "Sauvegarde échouée"}

    # Statistiques
    text = extract_text_from_html(html)
    stats = {
        "success": True,
        "url": group_url,
        "filepath": filepath,
        "html_size": len(html),
        "text_size": len(text),
        "scraped_at": datetime.now().isoformat(),
    }

    print(json.dumps(stats, indent=2))
    return stats


# ─── Point d'entrée ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)

    if not BRIGHT_DATA_ZONE:
        print("❌ BRIGHT_DATA_ZONE est requis. Ajoute-le dans .env")
        print("   BRIGHT_DATA_ZONE=sco_ai")
        sys.exit(1)

    print("=" * 50)
    print("🕵️  decroustra.AI — Scraper de groupes Facebook")
    print("=" * 50)
    print(f"🔑 Zone Bright Data : {BRIGHT_DATA_ZONE}")
    print()
    print("Groupes cibles :")
    for i, url in enumerate(GROUP_CANDIDATES, 1):
        print(f"  {i}. {url}")
    print()

    # Scraper tous les groupes
    for url in GROUP_CANDIDATES:
        print(f"\n--- {url} ---")
        scrape_and_save(url)
        print()

    print("✅ Jour 1 terminé ! Vérifie data/raw/ pour les résultats.")
