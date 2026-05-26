"""
search.py — Moteur de recherche pour les alertes de disparition

Permet de rechercher dans les alertes par lieu, âge, date, mot-clé.
"""

import json
import os
import re
from datetime import date, datetime

# ─── Configuration ───────────────────────────────────────────────────────────

DATA_DIR = "data"
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")


# ─── Moteur de recherche ─────────────────────────────────────────────────────


class AlertSearch:
    """Moteur de recherche pour les alertes de disparition"""

    def __init__(self, json_path: str = ALERTS_FILE):
        self.alerts = []
        self.load(json_path)

    def load(self, json_path: str):
        """Charge les alertes depuis le fichier JSON"""
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.alerts = data.get("alerts", [])
            print(f"[OK] {len(self.alerts)} alertes chargees")
        else:
            print(f"[WARN] Fichier {json_path} introuvable")

    # ─── Recherches ──────────────────────────────────────────────────────

    def search_by_location(self, location: str) -> list:
        """Trouve les alertes dans un lieu donné"""
        if not location:
            return []
        location = location.lower().strip()
        results = []
        for a in self.alerts:
            loc = (a.get("last_location") or "").lower()
            if location in loc:
                results.append(a)
        return results

    def search_by_age_range(self, min_age: int = 0, max_age: int = 120) -> list:
        """Trouve les alertes par tranche d'âge"""
        results = []
        for a in self.alerts:
            age = a.get("age")
            if age is not None and isinstance(age, (int, float)):
                if min_age <= age <= max_age:
                    results.append(a)
        return results

    def search_by_date_range(self, start_date: str, end_date: str) -> list:
        """Trouve les alertes sur une période"""
        results = []
        for a in self.alerts:
            d = a.get("disappearance_date")
            if d and isinstance(d, str):
                if start_date <= d <= end_date:
                    results.append(a)
        return results

    def search_keyword(self, keyword: str) -> list:
        """Recherche par mot-clé dans nom + lieu + contact"""
        if not keyword:
            return []
        keyword = keyword.lower().strip()
        results = []
        for a in self.alerts:
            text = " ".join(
                [
                    a.get("name") or "",
                    a.get("last_location") or "",
                    a.get("contact") or "",
                ]
            ).lower()
            if keyword in text:
                results.append(a)
        return results

    def search(self, query: str) -> list:
        """
        Recherche intelligente : detecte le type de requete
        et route vers la bonne methode.
        """
        query = query.strip()
        if not query:
            return []

        q = query.lower()

        # 1. Detection : "je recherche X" ou "mon fils X" ou "ma fille X"
        person_match = re.search(
            r"(?:je\s+(?:re)?cherche|mon\s+fils|ma\s+fille|mon\s+enfant|"
            r"recherche\s+(?:de|du|des|d'un|d'une)?)\s+(?:une?\s+)?"
            r"(?:personne|fille|garcon|homme|femme|enfant|fils)?\s*"
            r"(?:nommee?|appelee?|du\s+nom\s+(?:de\s+)?)?"
            r"([a-z][\w\s-]{2,30})",
            q,
        )
        if person_match:
            name = person_match.group(1).strip()
            # Chercher par nom d'abord
            results = self.search_keyword(name)
            if results:
                return results
            # Chercher par le mot complet
            results = self.search_keyword(query)
            if results:
                return results

        # 2. Detection : age ("11 ans", "10 ans", "X ans")
        age_match = re.search(r"(\d{1,2})\s*ans?", q)
        if age_match:
            age = int(age_match.group(1))
            # Chercher dans une plage autour de l'age
            results = self.search_by_age_range(max(0, age - 3), age + 3)
            if results:
                return results
            # Fallback : par mot-cle
            results = self.search_keyword(name) if person_match else []
            if results:
                return results

        # 3. Detection : enfants (< 18 ans)
        if any(
            w in q
            for w in [
                "enfant",
                "enfants",
                "mineur",
                "petit",
                "fils",
                "fille",
                "bebe",
                "ado",
            ]
        ):
            results = self.search_by_age_range(0, 17)
            if results:
                return results

        # 4. Detection : recherche par lieu
        location_match = re.search(r"(?:a|au|dans|sur)\s+(\w[\w\s-]+)", q)
        if location_match:
            loc = location_match.group(1).strip()
            results = self.search_by_location(loc)
            if results:
                return results

        # 5. Recherche par mot-cle
        results = self.search_keyword(query)
        if results:
            return results

        # 6. Fallback : recherche plus large par chaque mot
        for word in query.split():
            if len(word) > 2:
                results = self.search_keyword(word)
                if results:
                    return results

        # 7. Dernier recours : recherche par lieu
        return self.search_by_location(query)

    # ─── Utilitaires ─────────────────────────────────────────────────────

    def get_summary(self) -> dict:
        """Retourne un résumé des alertes"""
        missing = [a for a in self.alerts if a.get("status", "missing") == "missing"]

        # Âges
        ages = [a["age"] for a in self.alerts if a.get("age") is not None]

        # Localisations
        locations = {}
        for a in self.alerts:
            loc = a.get("last_location")
            if loc:
                # Extraction ville principale
                city = loc.split(",")[0].strip().lower()
                locations[city] = locations.get(city, 0) + 1

        # Ville la plus touchée
        top_city = max(locations, key=locations.get) if locations else None

        return {
            "total": len(self.alerts),
            "missing": len(missing),
            "resolved": len(self.alerts) - len(missing),
            "avg_age": round(sum(ages) / len(ages), 1) if ages else None,
            "min_age": min(ages) if ages else None,
            "max_age": max(ages) if ages else None,
            "top_location": (top_city, locations.get(top_city, 0))
            if top_city
            else None,
            "total_locations": len(locations),
        }

    def get_recent_alerts(self, days: int = 7) -> list:
        """Retourne les alertes récentes (dans les X derniers jours)"""
        today = date.today()
        results = []
        for a in self.alerts:
            d = a.get("disappearance_date")
            if d and isinstance(d, str):
                try:
                    alert_date = datetime.strptime(d, "%Y-%m-%d").date()
                    delta = (today - alert_date).days
                    if 0 <= delta <= days:
                        results.append(a)
                except ValueError:
                    pass
        return results

    def format_alert(self, alert: dict) -> str:
        """Formate une alerte pour l'affichage"""
        parts = []
        if alert.get("name"):
            parts.append(f"Personne: {alert['name']}")
        if alert.get("age") is not None:
            parts.append(f"{alert['age']} ans")
        if alert.get("gender"):
            parts.append(f"({alert['gender']})")
        if alert.get("last_location"):
            parts.append(f"Lieu: {alert['last_location']}")
        if alert.get("disappearance_date"):
            parts.append(f"Date: {alert['disappearance_date']}")
        if alert.get("contact"):
            parts.append(f"Contact: {alert['contact']}")

        return " | ".join(parts) if parts else "Alerte sans details"


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    search = AlertSearch()

    print("\n" + "=" * 50)
    print("[STATS] Resume general")
    print("=" * 50)
    summary = search.get_summary()
    for k, v in summary.items():
        print(f"   {k}: {v}")

    print("\n" + "=" * 50)
    print("[SEARCH] Tests de recherche")
    print("=" * 50)

    tests = [
        "Yopougon",
        "enfant",
        "Abidjan",
        "25",
    ]

    for test in tests:
        results = search.search(test)
        print(f'\n[QUERY] "{test}" -> {len(results)} resultat(s)')
        for r in results[:3]:
            print(f"   {search.format_alert(r)}")
        if len(results) > 3:
            print(f"   ... et {len(results) - 3} autre(s)")

    print("\n" + "=" * 50)
    print("[RECENT] Alertes recentes (30 jours)")
    print("=" * 50)
    recent = search.get_recent_alerts(30)
    for r in recent[:5]:
        print(f"   {search.format_alert(r)}")
    if len(recent) > 5:
        print(f"   ... et {len(recent) - 5} autre(s)")
