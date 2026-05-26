"""
run_extraction.py — Analyse massive de tous les posts Facebook via DeepSeek

Analyse TOUS les posts disponibles (pas de limite a 100)
Sauvegarde incrementielle pour ne rien perdre en cas d'erreur.
"""

import json
import re
import sys
from datetime import datetime, timezone

from openai import OpenAI

from config import DEEPSEEK_API_KEY

DATA_DIR = "data"
ALERTS_FILE = f"{DATA_DIR}/alerts.json"
FB_POSTS_FILE = "data/raw/fb_final.json"


def main():
    # 1. Charger les posts
    print("Chargement des posts...")
    try:
        with open(FB_POSTS_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        print(f"Fichier {FB_POSTS_FILE} introuvable.")
        print("Lance d'abord: python facebook_scraper.py")
        sys.exit(1)

    # 2. Extraire le texte pertinent
    texts = []
    for p in posts:
        content = ""
        orig = p.get("original_post", {})
        if orig and orig.get("content"):
            content = orig["content"]
        elif p.get("content"):
            content = p["content"]
        if content and len(content) > 60:
            texts.append(f"[{p.get('user_username_raw', '?')}] {content[:500]}")

    total_texts = len(texts)
    print(f"Posts avec texte: {total_texts} sur {len(posts)} total\n")

    # 3. Charger les alertes existantes
    if __import__("os").path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            existing_data = json.load(f)
            existing = existing_data.get("alerts", [])
    else:
        existing = []

    seen_names = {a.get("name", "") for a in existing if a.get("name")}
    print(f"Alertes existantes: {len(existing)}")
    print(f"Noms deja vus: {len(seen_names)}\n")

    # 4. Analyser par lots avec DeepSeek
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    all_persons = []
    batch_size = 20
    total_batches = (total_texts + batch_size - 1) // batch_size
    new_count = 0

    # Reprendre au lot specifie en argument
    start_batch = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if start_batch > 0:
        print(f"Reprise au lot {start_batch + 1}/{total_batches}\n")

    for batch_idx, batch_start in enumerate(range(0, total_texts, batch_size)):
        if batch_idx < start_batch:
            continue
        batch = texts[batch_start : batch_start + batch_size]
        batch_text = "\n---\n".join(batch)

        prompt = f"""Tu es un assistant specialise dans l'analyse de publications Facebook
de groupes d'alertes de disparition en Cote d'Ivoire.

Analyse ces posts et extrais TOUTES les personnes disparues mentionnees.

Pour chaque personne disparue, retourne :
- name : nom complet
- age : age (nombre, ou null)
- gender : "M", "F", ou null
- last_location : lieu de derniere apparition
- disappearance_date : date au format AAAA-MM-JJ (ou null)
- contact : numero de telephone (ou null)

POSTS A ANALYSER :
{batch_text}

Reponds UNIQUEMENT avec un JSON valide, sans autre texte :
{{"persons": [...]}}

Si aucune disparition trouvee : {{"persons": []}}
"""

        try:
            print(
                f"Lot {batch_idx + 1}/{total_batches} ({len(batch)} posts)... ",
                end="",
                flush=True,
            )
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            result = json.loads(content)
            persons = result.get("persons", [])

            # Filtrer les doublons
            for p in persons:
                name = p.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    p["status"] = "missing"
                    p["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    all_persons.append(p)
                    new_count += 1

            print(
                f"{len(persons)} extraites, {len([p for p in persons if p.get('name') not in seen_names])} nouvelles"
            )

            # Sauvegarde incrementielle tous les 10 lots
            if (batch_idx + 1) % 10 == 0:
                combined = existing + all_persons
                with open(ALERTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "total_alerts": len(combined),
                            "resolved_count": 0,
                            "last_updated": datetime.now(timezone.utc).isoformat(),
                            "alerts": combined,
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )

        except Exception as e:
            print(f"ERREUR: {e}")
            # Sauvegarder ce qu'on a deja
            if all_persons:
                combined = existing + all_persons
                with open(ALERTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "total_alerts": len(combined),
                            "resolved_count": 0,
                            "last_updated": datetime.now(timezone.utc).isoformat(),
                            "alerts": combined,
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
            continue

    # 5. Sauvegarde finale
    combined = existing + all_persons
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_alerts": len(combined),
                "resolved_count": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "alerts": combined,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n{'=' * 50}")
    print(f"TERMINE : {len(combined)} alertes totales")
    print(f"  Existantes : {len(existing)}")
    print(f"  Nouvelles  : {new_count}")
    print(f"  Fichier    : {ALERTS_FILE}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
