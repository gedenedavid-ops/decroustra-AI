"""
orchestrator.py — Pipeline complète decroustra.AI

Lance séquentiellement :
1. Facebook Scraper → posts bruts
2. Web Scraper → Google + sites d'actus
3. Extraction DeepSeek → analyse des posts
4. Déduplication + matching → nettoyage

Usage:
    python orchestrator.py           # Lance tout le pipeline
    python orchestrator.py --fb-only  # Facebook uniquement
    python orchestrator.py --web-only # Web uniquement
"""

import subprocess
import sys
import time
from datetime import datetime


def run_step(name: str, command: list[str]) -> bool:
    """Exécute une étape et retourne True si succès."""
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    start = time.time()
    try:
        result = subprocess.run(command, capture_output=False, text=True)
        elapsed = time.time() - start
        if result.returncode == 0:
            print(f"  {name} — OK ({elapsed:.1f}s)")
            return True
        else:
            print(f"  {name} — ÉCHEC (code {result.returncode})")
            return False
    except Exception as e:
        print(f"  {name} — ERREUR: {e}")
        return False


def main():
    print("=" * 60)
    print("  🕵️ decroustra.AI — Pipeline Hackathon")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    args = sys.argv[1:]
    run_fb = not args or "--fb-only" in args or ("--web-only" not in args)
    run_web = not args or "--web-only" in args or ("--fb-only" not in args)
    run_all = not args

    # Étape 1 : Facebook Scraper
    if run_fb or run_all:
        if not run_step(
            "Facebook Scraper (Bright Data)", [sys.executable, "facebook_scraper.py"]
        ):
            print("\n⚠️  Facebook scraping a échoué — on continue quand même...")

    # Étape 2 : Web Scraper (SERP + News)
    if run_web or run_all:
        if not run_step(
            "Web Scraper (SERP + News)", [sys.executable, "web_scraper.py"]
        ):
            print("\n⚠️  Web scraping a échoué — on continue quand même...")

    # Étape 3 : Extraction DeepSeek
    if run_all:
        if not run_step("Extraction DeepSeek", [sys.executable, "run_extraction.py"]):
            print("\n⚠️  Extraction échouée — on continue...")

    # Étape 4 : Déduplication + Matching
    if run_all:
        if not run_step("Déduplication + Matching", [sys.executable, "dedup.py"]):
            print("\n⚠️  Déduplication échouée")

    # Résumé final
    print("\n" + "=" * 60)
    print("  Pipeline terminée !")
    print(f"  Lance le frontend :  cd frontend && npm run dev")
    print(f"  Lance le backend  :  python app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
