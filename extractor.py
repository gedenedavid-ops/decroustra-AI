"""
extractor.py — Extraction des informations de disparition avec DeepSeek

Analyse le texte brut des groupes Facebook et extrait
les informations structurées (nom, âge, lieu, date, contact).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

from openai import OpenAI

from config import DEEPSEEK_API_KEY, validate_config
from scraper import RAW_DIR, extract_text_from_html, scrape_and_save

# ─── Configuration ───────────────────────────────────────────────────────────

DATA_DIR = "data"
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")
RESOLVED_FILE = os.path.join(DATA_DIR, "resolved.json")

# ─── Initialisation DeepSeek ─────────────────────────────────────────────────


def get_deepseek_client() -> OpenAI:
    """Retourne un client DeepSeek configuré"""
    if not DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY manquante. Configure .env d'abord.")
        sys.exit(1)

    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )


# ─── Pipeline d'extraction ────────────────────────────────────────────────────


def extract_missing_persons(text: str) -> list:
    """
    Utilise DeepSeek pour extraire les personnes disparues d'un texte.

    Args:
        text: Texte brut à analyser

    Returns:
        Liste de dicts avec les infos des disparitions
    """
    client = get_deepseek_client()

    # Nettoyer et limiter le texte
    text = text.strip()
    if not text:
        print("   ⚠️  Texte vide, rien à extraire")
        return []

    # Limiter à 8000 caractères (garder une marge pour le prompt)
    if len(text) > 8000:
        text = text[:8000] + "\n[...]"

    prompt = f"""Tu es un assistant qui analyse des publications Facebook
provenant de groupes d'alertes de disparition en Côte d'Ivoire.

Analyse ce texte et extrais TOUTES les personnes disparues mentionnées.

Pour chaque personne, retourne :
- name: nom complet (ou "Inconnu" si absent)
- age: âge en nombre (ou null si absent)
- gender: "M", "F", ou null
- last_location: lieu où vue pour la dernière fois
- disappearance_date: date au format AAAA-MM-JJ (ou null)
- contact: numéro de téléphone (ou null)

Règles importantes :
- Ne garde que les vraies disparitions, pas les annonces générales
- Si une personne est retrouvée, mets status à "resolved"
- Sois précis, ne fabrique pas d'informations

TEXTE À ANALYSER :
{text}

Réponds UNIQUEMENT avec un JSON valide, sans autre texte :
{{"persons": [...]}}

Si aucune disparition trouvée, réponds : {{"persons": []}}
"""

    try:
        print("   🤖 Appel DeepSeek...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Très bas pour être précis
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        # Nettoyer les éventuels markdown ```json ... ```
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        result = json.loads(content)
        persons = result.get("persons", [])

        print(f"   ✅ {len(persons)} disparition(s) trouvée(s)")
        return persons

    except json.JSONDecodeError as e:
        print(f"   ❌ Erreur JSON: {e}")
        print(f"   Réponse brute: {content[:200]}")
        return []
    except Exception as e:
        print(f"   ❌ Erreur DeepSeek: {e}")
        return []


def process_scraped_file(html_path: str, source_url: str = "") -> list:
    """
    Traite un fichier HTML scrapé et extrait les disparitions.

    Args:
        html_path: Chemin du fichier HTML
        source_url: URL source (pour le suivi)

    Returns:
        Liste des alertes structurées
    """
    print(f"\n📄 Traitement de : {os.path.basename(html_path)}")

    # 1. Extraire le texte du HTML
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    text = extract_text_from_html(html)
    print(f"   📝 {len(text)} caractères de texte extraits")

    if len(text) < 50:
        print("   ⚠️  Texte trop court, ignoré")
        return []

    # 2. Extraire les disparitions avec DeepSeek
    persons = extract_missing_persons(text)

    # 3. Enrichir avec les métadonnées
    alerts = []
    for i, person in enumerate(persons):
        alert = {
            "id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i + 1}",
            "name": person.get("name", "Inconnu"),
            "age": person.get("age"),
            "gender": person.get("gender"),
            "last_location": person.get("last_location", ""),
            "disappearance_date": person.get("disappearance_date"),
            "contact": person.get("contact"),
            "source_url": source_url,
            "source_file": os.path.basename(html_path),
            "status": person.get("status", "missing"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        alerts.append(alert)
        print(f"   👤 {alert['name']} — {alert.get('last_location', 'lieu inconnu')}")

    return alerts


# ─── Gestion des fichiers JSON ────────────────────────────────────────────────


def load_alerts() -> list:
    """Charge les alertes existantes"""
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("alerts", [])
    return []


def save_alerts(alerts: list):
    """Sauvegarde les alertes dans data/alerts.json"""
    os.makedirs(DATA_DIR, exist_ok=True)

    all_alerts = load_alerts() + alerts

    # Déduplication par ID
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

    print(f"\n💾 {len(unique)} alertes sauvegardées dans {ALERTS_FILE}")
    return unique


# ─── Pipeline complet ────────────────────────────────────────────────────────


def run_pipeline(scrape_new: bool = False):
    """
    Pipeline complet : scraping → extraction → sauvegarde

    Args:
        scrape_new: Si True, rescrape les groupes avant d'extraire
    """
    # 1. Scraper (optionnel)
    if scrape_new:
        print("=" * 50)
        print("🌐 Phase 1 : Scraping des groupes Facebook")
        print("=" * 50)
        from scraper import GROUP_CANDIDATES

        for url in GROUP_CANDIDATES:
            scrape_and_save(url)

    # 2. Lister les fichiers HTML disponibles
    html_files = []
    if os.path.exists(RAW_DIR):
        for f in sorted(os.listdir(RAW_DIR)):
            if f.endswith(".html"):
                html_files.append(os.path.join(RAW_DIR, f))

    if not html_files:
        print("❌ Aucun fichier HTML trouvé dans data/raw/")
        print("   Lance d'abord : python scraper.py")
        return

    print("=" * 50)
    print("🔍 Phase 2 : Extraction des disparitions")
    print("=" * 50)

    # 3. Extraire les personnes de chaque fichier
    all_alerts = []
    for html_path in html_files:
        source_url = ""  # On pourrait extraire l'URL du nom du fichier
        alerts = process_scraped_file(html_path, source_url)
        all_alerts.extend(alerts)

    # 4. Sauvegarder
    if all_alerts:
        save_alerts(all_alerts)
    else:
        print("\n⚠️  Aucune alerte trouvée dans les fichiers traités.")

    # 5. Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé")
    print("=" * 50)
    print(f"   Fichiers traités : {len(html_files)}")
    print(f"   Nouvelles alertes : {len(all_alerts)}")
    print(f"   Total dans la base : {len(load_alerts())}")
    print("=" * 50)


# ─── Point d'entrée ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)

    import argparse

    parser = argparse.ArgumentParser(description="Extraction des disparitions")
    parser.add_argument(
        "--scrape", action="store_true", help="Scraper les groupes avant d'extraire"
    )
    args = parser.parse_args()

    run_pipeline(scrape_new=args.scrape)
