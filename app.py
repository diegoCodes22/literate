from flask import Flask, session, redirect, request, render_template, jsonify
from helpers import login_required, generate_unique_id
from flask_session import Session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
import json

# Configure application
app = Flask(__name__)
app.debug = True

# Configure session to use filesystem instead of signed cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
database = "literate.sqlite"
conn = sqlite3.connect(database, check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


@login_required
def parse_deck_info(user_id=None, access=None):
    if user_id and not access:
        cur.execute("SELECT * FROM decks WHERE user_id=?", (user_id,))
    elif access and user_id:
        cur.execute("SELECT * FROM decks WHERE access=? AND user_id!=?", (access, user_id))
    decks = cur.fetchall()
    decks_list = []
    for deck in decks:
        dict(deck)
        deck_info = json.loads(deck["deck_info"])
        x = {"deck_name": deck["deck_name"], "word_count": len(deck_info["word"]),
             "deck_hash": deck["deck_hash"], "user_id": deck["user_id"], "learning": deck["learning"]}
        decks_list.append(x)
    return decks_list


@login_required
def paand(user_id, action, deck_hash=None, access=None, info=None, add=None):
    owner_id = None

    def community_share_check(deck_info_community_share):
        try:
            del deck_info['save-changes']
        except KeyError:
            pass
        try:
            if deck_info_community_share["community-share"][0] == "on":
                del deck_info["community-share"]
                return "Public"
            elif deck_info_community_share["community-share"][0] == "Private":
                del deck_info["community-share"]
                return "Private"
        except KeyError:
            return "Private"

    if deck_hash:
        cur.execute("SELECT * FROM decks WHERE deck_hash=?", (deck_hash,))
        deck = cur.fetchone()
        dict(deck)
        owner_id = deck["user_id"]
        if owner_id == user_id:
            scores = json.loads(deck["deck_info"])
            scores = scores["scores"]
            deck_info = request.form.to_dict(flat=False)
            deck_info["scores"] = scores
            if len(deck_info["scores"]) != len(deck_info["word"]):
                deck_info["scores"] += ["0"]*(len(deck_info["word"])-len(deck_info["scores"]))
        else:
            if add == "add":
                deck_info = request.form.to_dict(flat=False)
            else:
                deck_info = json.loads(deck["deck_info"])

            deck_info["scores"] = ["0"]*len(deck_info["word"])

        access = community_share_check(deck_info)

    elif info:
        deck_info = info
        access = access

    else:
        deck_info = request.form.to_dict(flat=False)
        deck_info["scores"] = ["0"]*len(deck_info["word"])
        access = community_share_check(deck_info)

    if action == "insert":
        if access == "Private":
            if info:
                cur.execute("INSERT INTO decks(user_id, deck_name, deck_info, access) "
                            "VALUES(?, ?, ?, ?)""RETURNING deck_id",
                            (user_id, info["deck-name"][0], json.dumps(info), access))
            else:
                cur.execute("INSERT INTO decks(user_id, deck_name, deck_info, access) "
                            "VALUES(?, ?, ?, ?)""RETURNING deck_id",
                            (user_id, deck_info["deck-name"][0], json.dumps(deck_info), access)
                            )
        else:
            cur.execute("INSERT INTO decks(user_id, deck_name, deck_info, access) VALUES(?, ?, ?, ?)"
                        "RETURNING deck_id",
                        (user_id, deck_info["deck-name"][0], json.dumps(deck_info), access))
        deck_id = cur.fetchone()[0]
        deck_hash = generate_unique_id(deck_id)
        cur.execute('UPDATE decks SET deck_hash=? WHERE deck_id=?', (deck_hash, deck_id))
        conn.commit()
        return 0

    elif action == "update" and owner_id == user_id:
        cur.execute("UPDATE decks SET deck_name=?, deck_info=?, access=? "
                    "WHERE user_id=? AND deck_hash=?",
                    (deck_info["deck-name"][0], json.dumps(deck_info), access, user_id,
                        deck_hash))
        conn.commit()
        return 0
    elif action == "update" and owner_id != user_id:
        deck_info["community-share"] = [access]
        paand(user_id, "insert", access="Private", info=deck_info)
        return 0
    else:
        return jsonify({"error": "Invalid action"})


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    user_id = session["user_id"]

    if request.method == "POST":
        inserted = paand(user_id, "insert")

        if inserted == 0:
            return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))
        else:
            return inserted

    else:
        return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))


@app.route("/start_page")
def start_page():
    return render_template("start_page.html")


@app.route("/login", methods=["POST", "GET"])
def login():

    session.clear()
    login_error = ""

    if request.method == "POST":
        cur.execute("SELECT * FROM users WHERE email=?", (request.form.get("email").lower(), ))
        user = cur.fetchone()

        if user is None:
            login_error = "Invalid email or password."
            return render_template("login.html", login_error=login_error)

        user = dict(user)

        if not check_password_hash(user["password_hash"], request.form.get("password")):
            login_error = "Invalid email or password."
            return render_template("login.html", login_error=login_error)
        else:
            session["user_id"] = user["id"]
            return redirect("/")
    else:
        return render_template("login.html", login_error=login_error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["POST", "GET"])
def register():

    if request.method == "POST":

        password_hash = generate_password_hash(request.form.get("password"))
        email = request.form.get("email").lower()

        cur.execute('INSERT INTO users (email, password_hash) VALUES(?, ?)',
                    (email, password_hash))
        conn.commit()

        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/email_availability", methods=["POST"])
def email_availability():
    if request.method == "POST":

        cur.execute("SELECT email FROM users WHERE email=?", (request.form.get("email").lower(),))

        if cur.fetchone():
            return jsonify({"available": False})
        else:
            return jsonify({"available": True})


@app.route("/create_deck")
@login_required
def create_deck():
    return render_template("create_deck.html")


@app.route("/edit", methods=["POST", "GET"])
@login_required
def edit_deck():

    deck_hash = request.args.get("dsh")
    user_id = session["user_id"]

    if request.method == "POST":

        paand(user_id, "update", deck_hash=deck_hash, add="add")

        return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))
    else:
        cur.execute("SELECT * FROM decks WHERE deck_hash=?", (deck_hash,))
        deck = cur.fetchone()
        deck = dict(deck)
        deck_info = json.loads(deck["deck_info"])
        word_def_ex = zip(deck_info["word"], deck_info["definition"], deck_info["example"])
        if deck["access"] == "Public":
            access = 1
        else:
            access = 0
        return render_template("edit.html", deck_info=word_def_ex, deck_name=deck["deck_name"], access=access,
                               deck_hash=deck_hash)


@app.route("/delete_deck", methods=["POST", "GET"])
@login_required
def delete_deck():
    if request.method == "GET":
        deck_hash = request.args.get("dsh")
        user_id = session["user_id"]
        cur.execute("SELECT user_id FROM decks WHERE deck_hash=?", (deck_hash,))
        try:
            owner_id = cur.fetchone()[0]
        except TypeError:
            return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))

        if owner_id == user_id:
            cur.execute("DELETE FROM decks WHERE deck_hash=?", (deck_hash,))
            conn.commit()
            return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))
        else:
            return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))


@app.route("/find_decks", methods=["POST", "GET"])
@login_required
def find_other_decks():
    if request.method == "GET":
        user_id = session["user_id"]
        return render_template("find_other_decks.html", decks_list=parse_deck_info(user_id=user_id, access="Public"))


@app.route("/save_other", methods=["POST", "GET"])
@login_required
def save_other():
    if request.method == "POST":
        user_id = session["user_id"]
        deck_hash = request.form.get("dsh")
        insert = paand(user_id, "update", deck_hash=deck_hash, access="Private")
        if insert == 0:
            return render_template("dashboard.html", decks_list=parse_deck_info(user_id=user_id))
        else:
            return insert


@app.route("/learning", methods=["POST", "GET"])
@login_required
def learning():
    if request.method == "POST":
        state = "On" if request.form.get("state") == "true" else "Off"
        deck_hash = request.form.get("dsh")
        cur.execute("UPDATE decks SET learning=? WHERE deck_hash=?", (state, deck_hash))
        conn.commit()
        return jsonify({"learning": state})


@app.route("/practice", methods=["POST", "GET"])
@login_required
def practice():
    if request.method == "GET":
        return render_template("practice.html")


@app.route("/practice_card", methods=["POST", "GET"])
@login_required
def practice_card():
    user_id = session["user_id"]

    if request.method == "GET":
        cur.execute("SELECT deck_info FROM decks WHERE user_id=? AND learning=?", (user_id, "On"))
        decks = cur.fetchall()

        cards = []

        if decks:
            for deck in decks:
                dict(deck)
                deck_info = json.loads(deck["deck_info"])
                print(deck_info)
                cards.append(list(zip(deck_info["word"], deck_info["definition"], deck_info["example"],
                                      deck_info["scores"])))

        algo_cards = []
        for card in cards:
            algo_cards += card

        algo_cards.sort(key=lambda scores: int(scores[3]))
        return json.dumps(algo_cards)
