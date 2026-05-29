"""
app.py - Serveur Flask API pour decroustra.AI
En dev: API uniquement (frontend sur http://localhost:5173)
En prod (Replit): sert le frontend React build
"""

import json
import os
import re

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI

from config import DEEPSEEK_API_KEY
from search import AlertSearch

# --- Initialisation ----------------------------------------------------------

app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
CORS(app)
app.config["JSON_AS_ASCII"] = False
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

_search_cache = None


def get_search():
    global _search_cache
    if _search_cache is None:
        _search_cache = AlertSearch()
    return _search_cache


# --- Frontend SPA ------------------------------------------------------------


# Servir les fichiers statiques du build React
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("frontend/dist/assets", filename)


@app.route("/favicon.svg")
def serve_favicon():
    return send_from_directory("frontend/dist", "favicon.svg")


# --- Routes API --------------------------------------------------------------


@app.route("/api")
def api_info():
    return jsonify(
        {"status": "decroustra.AI API v2", "endpoints": ["/api/ask", "/api/stats"]}
    )


@app.route("/api/stats")
def stats():
    search = get_search()
    summary = search.get_summary()
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


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "").strip()
    history = data.get("history", [])

    if not question:
        return jsonify({"answer": "Pose-moi une question sur les disparitions."})

    search = get_search()
    summary = search.get_summary()

    results = search.search(question)

    if not results:
        for word in question.split():
            if len(word) > 2:
                partial = search.search_keyword(word)
                if partial:
                    results = partial[:5]
                    break

    alerts_text = ""
    if results:
        for i, a in enumerate(results[:10], 1):
            name = a.get("name") or "Personne non identifiee"
            age = f"{a['age']} ans" if a.get("age") is not None else "Age inconnu"
            loc = a.get("last_location") or "Lieu inconnu"
            contact = a.get("contact") or "Non communique"
            alerts_text += (
                f"{i}. {name}, {age}, dernier vu a {loc}. Contact: {contact}\n"
            )

    system_prompt = f"""Tu es decroustra.AI, un assistant IA de centralisation des disparitions
en Cote d'Ivoire. Tu aides les familles a retrouver des personnes disparues.

Contexte: {summary["total"]} alertes, {summary.get("total_locations", 0)} localites.

Regles:
- Reponds en francais, texte simple, SANS markdown
- Utilise des tirets (-) pour les listes
- Garde le contexte de toute la conversation
- Ne redis JAMAIS bonjour si tu as deja repondu avant dans l'historique
- Sois direct et precis, evite les formules de politesse a repetition
"""

    messages = [{"role": "system", "content": system_prompt}]

    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})

    if results:
        user_msg = f"Question: {question}\n\nAlertes trouvees:\n{alerts_text}"
    else:
        user_msg = f"Question: {question}\n\n(Aucune alerte specifique trouvee. Reponds de maniere generale.)"

    messages.append({"role": "user", "content": user_msg})

    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.3,
        max_tokens=1000,
    )

    answer = response.choices[0].message.content
    answer = re.sub(r"\*\*([^*]+)\*\*", r"\1", answer)
    answer = re.sub(r"\*([^*]+)\*", r"\1", answer)
    answer = re.sub(r"`([^`]+)`", r"\1", answer)
    return jsonify({"answer": answer})


# --- SPA fallback (toute autre route -> index.html) -------------------------


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    # Si c'est une route API, ne pas interferer
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    # Sinon, servir le frontend React
    if os.path.exists("frontend/dist/index.html"):
        return send_from_directory("frontend/dist", "index.html")
    return jsonify(
        {"error": "Frontend not built. Run: cd frontend && npm run build"}
    ), 404


# --- Lancement ---------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("decroustra.AI")
    print("=" * 50)
    app.run(host="0.0.0.0", debug=False, port=5000)
