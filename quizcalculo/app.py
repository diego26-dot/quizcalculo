from flask import Flask, render_template, request, redirect, jsonify
import json, os, random
from datetime import datetime

app = Flask(__name__)

RANKING_FILE = "ranking.json"
SAVE_FILE = "save.json"
TEMAS_FILE = "temas.json"

# -------------------------------
# Funções utilitárias
# -------------------------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# -------------------------------
# Dados principais
# -------------------------------
temas = load_json(TEMAS_FILE, {
    "Esportes": [
        {"pergunta": "Quantas Copas o Brasil venceu?", "resposta": 5, "dificuldade": "Fácil"},
        {"pergunta": "Ano da primeira Copa (1930 - 1900)", "resposta": 30, "dificuldade": "Médio"},
        {"pergunta": "Medalhas em 2016 (19+1)", "resposta": 20, "dificuldade": "Difícil"}
    ],
    "Tecnologia": [
        {"pergunta": "Ano do 1º iPhone (2007-2000)", "resposta": 7, "dificuldade": "Fácil"},
        {"pergunta": "Bits em 1 byte?", "resposta": 8, "dificuldade": "Médio"},
        {"pergunta": "Ano do Google (1998-1990)", "resposta": 8, "dificuldade": "Difícil"}
    ]
})

ranking = load_json(RANKING_FILE, [])

save_state = load_json(SAVE_FILE, None)

# -------------------------------
# Rotas
# -------------------------------
@app.route("/")
def index():
    return render_template("index.html", temas=list(temas.keys()), has_save=bool(save_state))

@app.route("/ranking")
def page_ranking():
    return render_template("ranking.html", ranking=ranking)

@app.route("/temas")
def manage_temas():
    return render_template("manage_temas.html", temas=temas)

@app.route("/save-temas", methods=["POST"])
def save_temas():
    global temas
    temas = request.json
    save_json(TEMAS_FILE, temas)
    return jsonify({"ok": True})

@app.route("/single", methods=["POST"])
def single():
    tema = request.form["tema"]
    dificuldade = request.form["dificuldade"]
    nome_jogador = request.form["nome"]
    
    perguntas = [p for p in temas[tema] if p["dificuldade"] == dificuldade]
    random.shuffle(perguntas)

    qtd = int(request.form["quantidade"])
    perguntas = perguntas[:qtd]

    session = {
        "modo": "single",
        "tema": tema,
        "dificuldade": dificuldade,
        "nome": nome_jogador,
        "perguntas": perguntas,
        "index": 0,
        "acertos": 0
    }

    save_json(SAVE_FILE, session)

    return render_template("play_single.html", state=session)

@app.route("/single-answer", methods=["POST"])
def single_answer():
    session = load_json(SAVE_FILE, None)

    resp = request.form["resposta"]
    pergunta = session["perguntas"][session["index"]]

    correto = str(pergunta["resposta"])
    if resp == correto:
        session["acertos"] += 1

    session["index"] += 1
    save_json(SAVE_FILE, session)

    if session["index"] >= len(session["perguntas"]):
        ranking.append({
            "nome": session["nome"],
            "pontos": session["acertos"],
            "tema": session["tema"],
            "dificuldade": session["dificuldade"],
            "data": datetime.now().isoformat()
        })
        ranking.sort(key=lambda x: x["pontos"], reverse=True)
        save_json(RANKING_FILE, ranking)
        os.remove(SAVE_FILE)
        return redirect("/ranking")

    return render_template("play_single.html", state=session)

@app.route("/resume")
def resume():
    session = load_json(SAVE_FILE, None)
    if not session:
        return redirect("/")
    if session["modo"] == "single":
        return render_template("resume.html", state=session)
    else:
        return render_template("play_multi.html", state=session)

# ---------------- MULTIPLAYER ----------------
@app.route("/multi", methods=["POST"])
def multi():
    tema = request.form["tema"]
    dificuldade = request.form["dificuldade"]
    nome1 = request.form["nome1"]
    nome2 = request.form["nome2"]

    perguntas = [p for p in temas[tema] if p["dificuldade"] == dificuldade]
    random.shuffle(perguntas)
    qtd = int(request.form["quantidade"])
    perguntas = perguntas[:qtd]

    session = {
        "modo": "multi",
        "tema": tema,
        "dificuldade": dificuldade,
        "players": [nome1, nome2],
        "scores": {nome1: 0, nome2: 0},
        "perguntas": perguntas,
        "index": 0
    }

    save_json(SAVE_FILE, session)
    return render_template("play_multi.html", state=session)


@app.route("/multi-answer", methods=["POST"])
def multi_answer():
    session = load_json(SAVE_FILE, None)

    resp = request.form["resposta"]
    pergunta = session["perguntas"][session["index"]]
    player = session["players"][session["index"] % 2]
    correto = str(pergunta["resposta"])

    if resp == correto:
        session["scores"][player] += 1

    session["index"] += 1
    save_json(SAVE_FILE, session)

    if session["index"] >= len(session["perguntas"]):
        for p in session["players"]:
            ranking.append({
                "nome": p,
                "pontos": session["scores"][p],
                "tema": session["tema"],
                "dificuldade": session["dificuldade"],
                "data": datetime.now().isoformat()
            })
        ranking.sort(key=lambda x: x["pontos"], reverse=True)
        save_json(RANKING_FILE, ranking)
        os.remove(SAVE_FILE)
        return redirect("/ranking")

    return render_template("play_multi.html", state=session)


# -------------------------------
# Executar servidor
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
