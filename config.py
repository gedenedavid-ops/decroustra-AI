"""
Configuration du projet decroustra.AI
Charge les clés API depuis le fichier .env
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Bright Data ---
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_CUSTOMER_ID = os.getenv("BRIGHT_DATA_CUSTOMER_ID", "")
BRIGHT_DATA_ZONE = os.getenv("BRIGHT_DATA_ZONE", "")

# --- DeepSeek ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --- Sources par pays ---
SOURCES = {
    "CI": {
        "fb_groups": [
            "SOS ENFANTS DISPARUS DE COTE D'IVOIRE",
            "Avis de recherche Côte d'Ivoire",
        ],
        "news_sites": ["abidjan.net", "koaci.com", "linfodrome.ci"],
    },
    "BF": {
        "fb_groups": ["SOS Disparus Burkina Faso", "Avis de recherche Burkina"],
        "news_sites": ["lefaso.net", "sidwaya.info"],
    },
    "ML": {
        "fb_groups": ["Avis de recherche Mali", "SOS Disparus Mali"],
        "news_sites": ["maliweb.net", "malijet.com"],
    },
    "SN": {
        "fb_groups": ["SOS Disparus Sénégal", "Avis de recherche Sénégal"],
        "news_sites": ["seneweb.com", "dakaractu.com"],
    },
}


# --- Validation ---
def validate_config():
    """Vérifie que les clés API sont présentes au démarrage"""
    missing = []
    if not BRIGHT_DATA_API_KEY:
        missing.append("BRIGHT_DATA_API_KEY")
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")

    if missing:
        print(f"⚠️  Clés API manquantes dans .env : {', '.join(missing)}")
        print(f"   Copie .env.example → .env et ajoute tes clés.")
        return False
    return True


if __name__ == "__main__":
    validate_config()
