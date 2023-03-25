from flask import Flask, session, redirect, request, render_template, jsonify
from helpers import login_required, generate_unique_id
from flask_session import Session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
import json

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
def dashboard_deck_info():
    user_id = session["user_id"]
    decks = cur.execute("SELECT * FROM decks WHERE user_id=?", (user_id,))
    decks = cur.fetchall()
    decks_list = []
    for deck in decks:
        dict(deck)
        deck_info = json.loads(deck["deck_info"])
        x = {"deck_name": deck["deck_name"], "word_count": len(deck_info["word"]),
             "deck_hash": deck["deck_hash"]}
        decks_list.append(x)
    return decks_list


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
        community_share = "Private"
        access_list = None

        deck_info = request.form.to_dict(flat=False)
        deck_name = deck_info['deck-name'][0]

        try:
            if deck_info["community-share"][0] == "on":
                community_share = "Public"
                del deck_info["community-share"]
        except KeyError:
            access_list = [user_id]

        del deck_info['save-changes']

        cur.execute("INSERT INTO decks(user_id, deck_name, deck_info, access, access_list) VALUES(?, ?, ?, ?, ?)",
                    (user_id, deck_name, json.dumps(deck_info), community_share, json.dumps(access_list)))
        conn.commit()

        deck_id = cur.execute("SELECT deck_id FROM decks WHERE user_id=? AND deck_name=?", (user_id, deck_name))
        deck_id = cur.fetchone()[0]
        deck_id = generate_unique_id(deck_id)
        cur.execute("UPDATE decks SET deck_hash=? WHERE user_id=? AND deck_name=?", (deck_id, user_id, deck_name))
        conn.commit()

        return render_template("dashboard.html", decks_list=dashboard_deck_info())

    else:
        return render_template("dashboard.html", decks_list=dashboard_deck_info())


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

        # I don't know why I wrote this line, I comment it just in case
        # cur.execute("SELECT id FROM users")

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
    # deck_id = request.args.get("deck_id")
    deck_hash = request.args.get("deck_hash")
    user_id = session["user_id"]
    community_share = "Private"
    if request.method == "POST":

        deck_info = request.form.to_dict(flat=False)
        deck_name = deck_info['deck-name'][0]

        try:
            if deck_info["community-share"][0] == "on":
                community_share = "Public"
        except KeyError:
            pass

        del deck_info['save-changes']

        cur.execute("UPDATE decks SET deck_name=?, deck_info=?, access=? WHERE deck_hash=?",
                    (deck_name, json.dumps(deck_info), community_share, deck_hash))
        conn.commit()

        return render_template("dashboard.html", decks_list=dashboard_deck_info())
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
