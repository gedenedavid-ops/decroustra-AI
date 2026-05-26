"""
app.py — Serveur Flask avec interface chat pour decroustra.AI

Route /ask : reçoit une question, cherche dans les alertes, répond via DeepSeek
Route /stats : retourne les statistiques des alertes
"""

import json
import os
import re
from datetime import date

from flask import Flask, jsonify, render_template, request
from openai import OpenAI

from config import DEEPSEEK_API_KEY
from search import AlertSearch

# ─── Initialisation ──────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# Cache pour le moteur de recherche (evite de reload le JSON a chaque requete)
_search_cache = None


def get_search():
    global _search_cache
    if _search_cache is None:
        _search_cache = AlertSearch()
    return _search_cache


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stats")
def stats():
    search = get_search()
    summary = search.get_summary()
    # Lire les stats enrichies depuis alerts.json
    resolved = 0
    groups = 0
    try:
        with open("data/alerts.json", "r") as f:
            d = json.load(f)
            resolved = d.get("resolved_count", 0)
            groups = d.get("duplicate_groups", 0)
    except:
        pass
    return jsonify(
        {
            "total": summary["total"],
            "missing": summary["missing"] - resolved,
            "resolved": resolved,
            "cities": summary.get("total_locations", 0),
            "duplicate_groups": groups,
        }
    )


@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Pose-moi une question sur les disparitions."})

    search = get_search()
    summary = search.get_summary()

    # 1. Chercher les résultats
    results = search.search(question)

    if not results:
        # Essayer une recherche plus large
        for word in question.split():
            if len(word) > 2:
                partial = search.search_keyword(word)
                if partial:
                    results = partial[:5]
                    break

    if not results:
        # Reponse utile quand rien trouve
        return jsonify(
            {
                "answer": (
                    f"Je n'ai pas trouve d'alerte correspondant exactement a ta recherche.\n\n"
                    f"Notre base contient actuellement {summary['total']} alertes "
                    f"dans {summary.get('total_locations', 0)} localites.\n\n"
                    f"Essaie un lieu (Yopougon, Abidjan, Abobo...), "
                    f"une tranche d'age (enfants, enfants disparus...), "
                    f"ou demande le resume general.\n\n"
                    f"N'hesite pas a essayer differentes formulations."
                )
            }
        )

    # 2. Formater les resultats pour DeepSeek (texte simple)
    alerts_text = ""
    for i, a in enumerate(results[:10], 1):
        name = a.get("name") or "Personne non identifiee"
        age = f"{a['age']} ans" if a.get("age") is not None else "Age inconnu"
        loc = a.get("last_location") or "Lieu inconnu"
        contact = a.get("contact") or "Non communique"
        alerts_text += f"{i}. {name}, {age}, dernier vu a {loc}. Contact: {contact}\n"

    # 3. Generer la reponse avec DeepSeek
    prompt = f"""Tu es decroustra.AI, un assistant de centralisation des disparitions
en Cote d'Ivoire. Tu aides les familles a retrouver des personnes disparues.

Contexte actuel:
- {summary["total"]} alertes dans la base de donnees
- {summary.get("total_locations", 0)} villes/localites couvertes
- Age moyen des disparus: {summary.get("avg_age", "?")} ans

Question de l'utilisateur: {question}

Alertes correspondantes trouvees:
{alerts_text}

Regles:
- Reponds UNIQUEMENT en francais, en texte simple SANS markdown, SANS asterisques, SANS mise en forme
- Utilise des tirets simples (-) pour les listes, pas de **gras** ni de *italique*
- Cite les informations pertinentes (nom, lieu, contact)
- Sois clair, precis et bienveillant
- Propose d'affiner la recherche si pertinent
- N'invente PAS d'informations
- Si des resultats sont hors Côte d'Ivoire, mentionne-le clairement
"""

    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )

    answer = response.choices[0].message.content
    # Nettoyer le markdown eventuel
    import re

    answer = re.sub(r"\*\*([^*]+)\*\*", r"\1", answer)  # **gras** -> gras
    answer = re.sub(r"\*([^*]+)\*", r"\1", answer)  # *italique* -> italique
    answer = re.sub(r"`([^`]+)`", r"\1", answer)  # `code` -> code
    return jsonify({"answer": answer})


# ─── Lancement ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("decroustra.AI - Serveur demarre")
    print("http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000)
