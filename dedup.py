"""
dedup.py — Détection de doublons et appariement Disparus/Retrouvés

Features :
1. Détecter les mêmes personnes signalées plusieurs fois
2. Apparier un avis de disparition avec un "retrouvé"
3. Mettre à jour le statut des alertes
"""

import json
import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

# ─── Configuration ───────────────────────────────────────────────────────────

DATA_DIR = "data"
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")


# ─── Outils de similarité ────────────────────────────────────────────────────


def sim(a: str, b: str) -> float:
    """Similarité entre deux chaînes (0.0 à 1.0)"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def extract_keywords(text: str) -> set:
    """Extrait les mots-clés significatifs d'un texte"""
    words = set(re.findall(r"\b[a-zà-ÿ]{4,}\b", text.lower()))
    stopwords = {
        "avec",
        "dans",
        "pour",
        "sur",
        "tout",
        "plus",
        "bien",
        "fait",
        "faire",
        "être",
        "avoir",
        "cette",
        "leurs",
        "tous",
        "sont",
        "aussi",
        "très",
        "assez",
        "peu",
        "peut",
        "doit",
        "peux",
        "encore",
        "entre",
        "chez",
        "avis",
        "alerte",
        "recherche",
        "disparition",
        "partagez",
    }
    return words - stopwords


# ─── Dédoublonnage ──────────────────────────────────────────────────────────


def find_duplicates(alerts: list) -> list:
    """
    Trouve les alertes qui parlent probablement de la même personne.
    Retourne des groupes d'alertes similaires.
    """
    groups = []
    processed = set()

    # Indexer les alertes par premier mot du nom pour accelerer
    by_name = {}
    for i, a in enumerate(alerts):
        name = (a.get("name") or "").strip().lower()
        if name:
            first_word = name.split()[0] if name.split() else name
            if first_word not in by_name:
                by_name[first_word] = []
            by_name[first_word].append(i)

    for i, a in enumerate(alerts):
        if i in processed:
            continue

        group = [a]
        processed.add(i)

        # Chercher uniquement les alertes avec le meme premier mot de nom
        name_a = (a.get("name") or "").strip().lower()
        candidates = []
        if name_a:
            first = name_a.split()[0] if name_a.split() else name_a
            for idx in by_name.get(first, []):
                if idx != i and idx not in processed:
                    candidates.append(idx)

        for j in candidates:
            score = 0.0
            reasons = []

            # Comparaison par nom
            name_a = (a.get("name") or "").strip()
            name_b = (alerts[j].get("name") or "").strip()
            if name_a and name_b:
                s = sim(name_a, name_b)
                if s > 0.7:
                    score += s * 3
                    reasons.append(f"nom: {s:.0%}")

            # Comparaison par lieu
            loc_a = (a.get("last_location") or "").strip()
            loc_b = (alerts[j].get("last_location") or "").strip()
            if loc_a and loc_b:
                s = sim(loc_a, loc_b)
                if s > 0.5:
                    score += s * 2
                    reasons.append(f"lieu: {s:.0%}")

            # Comparaison par contact
            contact_a = (a.get("contact") or "").strip()
            contact_b = (alerts[j].get("contact") or "").strip()
            if contact_a and contact_b and contact_a[:6] == contact_b[:6]:
                score += 2
                reasons.append("contact similaire")

            # Comparaison par âge
            age_a = a.get("age")
            age_b = alerts[j].get("age")
            if age_a and age_b and abs(age_a - age_b) <= 2:
                score += 1
                reasons.append("âge proche")

            # Seuil de confiance
            if score >= 2.5:
                group.append(alerts[j])
                processed.add(j)

        if len(group) > 1:
            groups.append(
                {
                    "alerts": group,
                    "size": len(group),
                    "score": round(score, 1),
                    "reasons": reasons,
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return groups


# ─── Appariement Disparu → Retrouvé ───────────────────────────────────────


def find_resolved(alerts: list) -> list:
    """
    Cherche des posts "RETROUVÉ / TROUVÉ" et les apparie
    avec des disparitions actives.
    """
    # 1. Identifier les alertes "retrouvé"
    resolved_keywords = [
        r"\bretrouvé\b",
        r"\btrouvé\b",
        r"\brétabli\b",
        r"\bretrouvée\b",
        r"\btrouvée\b",
        r"\bsaine et sauve\b",
        r"\bsain et sauf\b",
        r"\bretrouvé vivant\b",
        r"\bretrouvé sain\b",
        r"\bretrouvée saine\b",
        r"\bde retour\b",
        r"\best rentré\b",
        r"\best rentrée\b",
    ]

    resolved_alerts = []
    missing_alerts = []

    for a in alerts:
        text = " ".join(
            [
                a.get("title") or "",
                a.get("snippet") or "",
                a.get("content") or "",
            ]
        ).lower()

        # Vérifier si c'est un post de type "retrouvé"
        is_resolved = any(re.search(kw, text) for kw in resolved_keywords)

        if is_resolved:
            resolved_alerts.append(a)
        elif a.get("status") in ("missing", None, "", "pending"):
            missing_alerts.append(a)

    # 2. Apparier chaque "retrouvé" avec des disparitions
    matches = []
    for r_alert in resolved_alerts:
        text = " ".join(
            [
                r_alert.get("title") or "",
                r_alert.get("snippet") or "",
                r_alert.get("content") or "",
            ]
        ).lower()

        # Extraire les mots-clés du post "retrouvé"
        keywords = extract_keywords(text)

        best_match = None
        best_score = 0.0

        for m_alert in missing_alerts:
            score = 0.0
            name = (m_alert.get("name") or "").lower()
            loc = (m_alert.get("last_location") or "").lower()

            # Score basé sur le nom
            if name:
                name_words = set(name.split())
                overlap = name_words & keywords
                score += len(overlap) * 2

                # Vérifier si le nom apparaît dans le texte
                if name in text:
                    score += 3

            # Score basé sur le lieu
            if loc:
                loc_words = set(loc.split())
                overlap = loc_words & keywords
                score += len(overlap)

            if score > best_score:
                best_score = score
                best_match = m_alert

        # Seuil : au moins 3 points de similarité
        if best_match and best_score >= 3:
            matches.append(
                {
                    "resolved_alert": r_alert,
                    "matched_missing": best_match,
                    "confidence": round(best_score / 10, 2),
                    "matched_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return matches


# ─── Mise à jour du statut ─────────────────────────────────────────────────


def update_alerts(matches: list, groups: list) -> int:
    """
    Met à jour alerts.json :
    - Marque les disparitions appariées comme "resolved"
    - Ajoute les IDs des doublons
    """
    if not os.path.exists(ALERTS_FILE):
        print("❌ alerts.json introuvable")
        return 0

    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    alerts = data.get("alerts", [])
    updated_count = 0

    # S'assurer que chaque alerte a un id
    for i, a in enumerate(alerts):
        if "id" not in a or not a["id"]:
            a["id"] = f"auto_{i}_{abs(hash(str(a.get('name', '')) + str(i))) % 10**6}"

    # Marquer les résolus
    resolved_ids = set()
    for m in matches:
        matched = m["matched_missing"]
        alert_id = matched.get("id")
        if alert_id:
            for a in alerts:
                if a["id"] == alert_id:
                    old_status = a.get("status", "missing")
                    if old_status != "resolved":
                        a["status"] = "resolved"
                        a["resolved_at"] = m["matched_at"]
                        a["resolved_by"] = m["resolved_alert"].get("id", "auto")
                        a["confidence"] = m["confidence"]
                        resolved_ids.add(alert_id)
                        updated_count += 1

    # Marquer les doublons
    for g in groups:
        if len(g["alerts"]) >= 2:
            main_id = g["alerts"][0].get("id")
            dup_ids = [a.get("id") for a in g["alerts"][1:] if a.get("id")]
            for a in alerts:
                if a["id"] == main_id:
                    existing = a.get("duplicate_ids", [])
                    for d in dup_ids:
                        if d not in existing:
                            existing.append(d)
                    a["duplicate_ids"] = existing
                    a["duplicate_count"] = len(existing) + 1

    # Stats
    data["total_alerts"] = len(alerts)
    data["resolved_count"] = len([a for a in alerts if a.get("status") == "resolved"])
    data["duplicate_groups"] = len(groups)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated_count


# ─── Pipeline ────────────────────────────────────────────────────────────────


def run():
    if not os.path.exists(ALERTS_FILE):
        print("[ERROR] alerts.json introuvable")
        return

    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    alerts = data.get("alerts", [])
    print(f"[LOAD] {len(alerts)} alertes chargees")
    print()

    # 1. Dédoublonnage
    print("-" * 40)
    print("DEDUPLICATION")
    print("-" * 40)
    groups = find_duplicates(alerts)
    if groups:
        print(f"   [OK] {len(groups)} groupe(s) de doublons detecte(s)")
        for g in groups:
            names = [a.get("name") or "?" for a in g["alerts"]]
            print(f"   • {', '.join(names)} (score: {g['score']})")
    else:
        print("   [INFO] Aucun doublon detecte")

    print()

    # 2. Appariement
    print("-" * 40)
    print("MATCHING DISPARUS -> RETROUVES")
    print("-" * 40)
    matches = find_resolved(alerts)
    if matches:
        print(f"   [OK] {len(matches)} appariement(s) trouve(s)")
        for m in matches:
            found = m["resolved_alert"]
            missing = m["matched_missing"]
            found_text = (found.get("title") or found.get("snippet") or "")[:100]
            missing_name = missing.get("name") or "?"
            print(f"   • «{missing_name}» ← «{found_text}...»")
            print(f"     Confiance: {m['confidence']:.0%}")
    else:
        print("   [INFO] Aucun appariement trouve")

    print()

    # 3. Mise à jour
    print("-" * 40)
    print("UPDATE")
    print("-" * 40)
    updated = update_alerts(matches, groups)
    print(f"   [OK] {updated} alerte(s) resolue(s)")

    # 4. Nouvelles stats
    with open(ALERTS_FILE, "r") as f:
        data = json.load(f)

    total = data["total_alerts"]
    resolved = data.get("resolved_count", 0)
    missing_total = total - resolved

    print()
    print("=" * 40)
    print("NOUVELLES STATISTIQUES")
    print("=" * 40)
    print(f"   Total alertes:   {total}")
    print(f"   Disparus:        {missing_total}")
    print(f"   Retrouvés:       {resolved}")
    print(f"   Groupes doublons:{data.get('duplicate_groups', 0)}")
    print("=" * 40)


if __name__ == "__main__":
    run()
