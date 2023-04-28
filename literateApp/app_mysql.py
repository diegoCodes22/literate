# Server
from flask import Flask, session, redirect, request, render_template, jsonify
from flask_session import Session
from waitress import serve

# Functions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, generate_unique_id

# Database
import sqlalchemy
from connect_unix import connect_unix_socket

# Data
from json import loads, dumps

# Emails
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Error handling
from sqlalchemy.exc import IntegrityError


# Email config
feedback_email = "literate22@outlook.com"
sender_pass = "nefpy0-wycdEj-mocrid"

# Configure application
app = Flask(__name__)
# app.debug = True

# Configure session to use filesystem instead of signed cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
db = connect_unix_socket()


@login_required
def parse_deck_info(dbs, user_id=None, access=None):
    with dbs.connect() as cur:
        if user_id and not access:
            stmt = sqlalchemy.text("SELECT * FROM decks WHERE user_id=:user_id")
            decks = cur.execute(stmt, parameters={"user_id": user_id}).mappings().all()
        elif access == "Public" and user_id:
            stmt = sqlalchemy.text("SELECT * FROM decks WHERE access=:access AND user_id!=:user_id")
            decks = cur.execute(stmt, parameters={"access": access, "user_id": user_id}).mappings().all()
    decks_list = []
    for deck in decks:
        deck_info = loads(deck["deck_info"])
        x = {"deck_name": deck["deck_name"], "word_count": len(deck_info["word"]),
             "deck_hash": deck["deck_hash"], "user_id": deck["user_id"], "learning": deck["learning"]}
        decks_list.append(x)
    return decks_list


@login_required
def render_stats(dbs):
    user_id = session["user_id"]
    stmt = sqlalchemy.text("SELECT deck_info FROM decks WHERE user_id=:user_id")
    with dbs.connect() as cur:
        decks = cur.execute(stmt, parameters={"user_id": user_id}).mappings().all()

        word_count = 0
        words_mastered = 0

        for deck in decks:
            deck_info = loads(deck["deck_info"])
            word_count += len(deck_info["word"])

            # To make words_mastered show the mastered words, I need enumerate,
            # because I will have to access deck_info["word"][i]
            for i, score in enumerate(deck_info["scores"]):
                if int(score) >= 15:
                    words_mastered += 1

    return word_count, words_mastered


@login_required
def paand(dbs, user_id, action, deck_hash=None, access=None, info=None, add=None):
    # owner_id = None

    def community_share_check(deck_info_community_share):
        try:
            del deck_info['save-changes']
        except KeyError:
            pass
        try:  # community-share does not need to be refactored, this is the only place I use it, it comes from the
            # html and js, where the slider for sharing is idd community-share
            if deck_info_community_share["community-share"][0] == "on":
                del deck_info["community-share"]
                return "Public"
            elif deck_info_community_share["community-share"][0] == "Private":
                del deck_info["community-share"]
                return "Private"
        except KeyError:
            return "Private"

    with dbs.connect() as cur:
        if deck_hash:  # SQL Refactoring
            deck = cur.execute(sqlalchemy.text("SELECT * FROM decks WHERE deck_hash=:deck_hash"),
                               parameters={"deck_hash": deck_hash}).mappings().all()

            owner_id = deck[0]["user_id"]

            if owner_id == user_id:
                scores = loads(deck[0]["deck_info"])['scores']
                deck_info = request.form.to_dict(flat=False)
                deck_info["scores"] = scores
                if len(deck_info["scores"]) != len(deck_info["word"]):
                    deck_info["scores"] += ["0"]*(len(deck_info["word"])-len(deck_info["scores"]))
            else:
                if add == "add":
                    deck_info = request.form.to_dict(flat=False)
                else:
                    deck_info = loads(deck[0]["deck_info"])

                deck_info["scores"] = ["0"]*len(deck_info["word"])

            access = community_share_check(deck_info)

        elif info:
            deck_info = info
            access = access

        else:
            deck_info = request.form.to_dict(flat=False)
            deck_info["scores"] = ["0"]*len(deck_info["word"])
            access = community_share_check(deck_info)

        # maybe deck_name[0] -> deck_name
        if action == "insert":
            insert_stmt = sqlalchemy.text("INSERT INTO decks (user_id, deck_name, deck_info, access) "
                                          "VALUES (:user_id, :deck_name, :deck_info, :access)")
            params = {"user_id": user_id, "deck_name": deck_info["deck_name"][0], "deck_info": dumps(deck_info), "access": access}

            cur.execute(insert_stmt, params)

            deck_id = cur.execute(sqlalchemy.text("SELECT LAST_INSERT_ID()")).fetchone()

            cur.execute(sqlalchemy.text("UPDATE decks SET deck_hash=:deck_hash WHERE deck_id=:deck_id"),
                        parameters={"deck_hash": generate_unique_id(deck_id[0]), "deck_id": deck_id[0]})
            cur.commit()
            return 0

        # maybe deck_name[0] -> deck_name
        elif action == "update" and owner_id == user_id:
            cur.execute(sqlalchemy.text("UPDATE decks SET deck_name=:deck_name, deck_info=:deck_info, access=:access "
                                        "WHERE user_id=:user_id AND deck_hash=:deck_hash"),
                        parameters={"deck_name": deck_info["deck_name"][0], "deck_info": dumps(deck_info),
                                    "access": access, "user_id": user_id, "deck_hash": deck_hash})
            cur.commit()
            return 0
        elif action == "update" and owner_id != user_id:
            deck_info["community-share"] = [access]
            paand(dbs, user_id, "insert", access="Private", info=deck_info)
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
        inserted = paand(db, user_id, "insert")

        if inserted == 0:
            return redirect("/")
        else:
            return inserted

    else:
        return render_template("/index.html", decks_list=parse_deck_info(db, user_id=user_id), stats=render_stats(db))


@app.route("/start_page")
def start_page():
    return render_template("/start_page.html")


@app.route("/login", methods=["POST", "GET"])
def login():

    session.clear()
    login_error = "Invalid email or password."

    if request.method == "POST":
        stmt = sqlalchemy.text("SELECT * FROM users WHERE email=:email")
        with db.connect() as cur:
            user = cur.execute(stmt, parameters={"email": request.form.get("email").lower()}).mappings().all()

        try:
            if user[0]['email'] and check_password_hash(user[0]['password_hash'], request.form.get("password")):
                session["user_id"] = user[0]["id"]
                return redirect("/")
            else:
                pass
        except IndexError:
            pass
        return render_template("/login.html", login_error=login_error)

    else:
        return render_template("/login.html", login_error="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["POST", "GET"])
def register():

    if request.method == "POST":

        password_hash = generate_password_hash(request.form.get("password"))
        email = request.form.get("email").lower()

        stmt = sqlalchemy.text("INSERT INTO users (email, password_hash) VALUES(:email, :password_hash)")
        stmt2 = sqlalchemy.text("SELECT LAST_INSERT_ID()")

        with db.connect() as cur:
            try:
                cur.execute(stmt, parameters={"email": email, "password_hash": password_hash})
            except sqlalchemy.exc.IntegrityError:
                return render_template("/register")

            u_id = cur.execute(stmt2).fetchone()
            cur.commit()
            session["user_id"] = u_id[0]
        return redirect("/")

    else:
        return render_template("/register.html")


@app.route("/email_availability", methods=["POST"])
def email_availability():
    if request.method == "POST":
        stmt = sqlalchemy.text("SELECT email FROM users WHERE email=:email")
        with db.connect() as cur:
            email = cur.execute(stmt, parameters={"email": request.form.get("email").lower()}).fetchone()

            if email is not None:
                return jsonify({"available": False})
            else:
                return jsonify({"available": True})


@app.route("/create_deck")
@login_required
def create_deck():
    return render_template("/create_deck.html")


@app.route("/edit", methods=["POST", "GET"])
@login_required
def edit_deck():

    deck_hash = request.args.get("dsh")

    if request.method == "POST":
        user_id = session["user_id"]

        paand(db, user_id, "update", deck_hash=deck_hash, add="add")
        return redirect("/")
    else:
        stmt = sqlalchemy.text("SELECT * FROM decks WHERE deck_hash=:deck_hash")
        with db.connect() as cur:
            deck = cur.execute(stmt, parameters={"deck_hash": deck_hash}).mappings().all()
            deck_info = loads(deck[0]["deck_info"])
            word_def_ex = zip(deck_info["word"], deck_info["definition"], deck_info["example"])
            if deck[0]["access"] == "Public":
                access = 1
            else:
                access = 0
            return render_template("/edit.html", deck_info=word_def_ex, deck_name=deck[0]["deck_name"], access=access,
                                   deck_hash=deck_hash)


# Test redirect vs render_template
@app.route("/delete_deck", methods=["POST", "GET"])
@login_required
def delete_deck():
    if request.method == "GET":
        deck_hash = request.args.get("dsh")
        user_id = session["user_id"]
        u_id_stmt = sqlalchemy.text("SELECT user_id FROM decks WHERE deck_hash=:deck_hash")
        del_stmt = sqlalchemy.text("DELETE FROM decks WHERE deck_hash=:deck_hash")
        with db.connect() as cur:
            try:
                owner_id = cur.execute(u_id_stmt, parameters={"deck_hash": deck_hash}).fetchone()[0]
            except TypeError:
                # return render_template("/index.html", decks_list=parse_deck_info(user_id=user_id))
                return redirect("/")

            if owner_id == user_id:
                cur.execute(del_stmt, parameters={"deck_hash": deck_hash})
                cur.commit()
                return redirect("/")
            else:
                # return render_template("/index.html", decks_list=parse_deck_info(user_id=user_id))
                return redirect("/")


@app.route("/find_decks", methods=["POST", "GET"])
@login_required
def find_other_decks():
    if request.method == "GET":
        user_id = session["user_id"]
        return render_template("/find_other_decks.html", decks_list=parse_deck_info(db, user_id=user_id, access="Public"))


@app.route("/save_other", methods=["POST", "GET"])
@login_required
def save_other():
    if request.method == "POST":
        user_id = session["user_id"]
        deck_hash = request.form.get("dsh")
        insert = paand(db, user_id, "update", deck_hash=deck_hash, access="Private")
        if insert == 0:
            return redirect("/")
        else:
            return insert


@app.route("/learning", methods=["POST", "GET"])
@login_required
def learning():
    if request.method == "POST":
        state = "On" if request.form.get("state") == "true" else "Off"
        deck_hash = request.form.get("dsh")
        stmt = sqlalchemy.text("UPDATE decks SET learning=:learning WHERE deck_hash=:deck_hash")
        with db.connect() as cur:
            cur.execute(stmt, parameters={"learning": state, "deck_hash": deck_hash})
            cur.commit()
            return jsonify({"learning": state})


@app.route("/practice", methods=["POST", "GET"])
@login_required
def practice():
    if request.method == "GET":
        return render_template("/practice.html")


@app.route("/practice_card", methods=["POST", "GET"])
@login_required
def practice_card():
    user_id = session["user_id"]

    def learning_decks():

        l_stmt = sqlalchemy.text("SELECT deck_info, deck_hash FROM decks WHERE user_id=:user_id AND learning=:learning")
        with db.connect() as l_cur:
            decks = l_cur.execute(l_stmt, parameters={"user_id": user_id, "learning": "On"}).mappings().all()

        l_cards = []

        if decks:
            for deck in decks:
                cards_dic = {}
                l_deck_info = loads(deck["deck_info"])
                cards_dic["cards"] = (list(zip(l_deck_info["word"], l_deck_info["definition"], l_deck_info["example"],
                                           l_deck_info["scores"])))
                cards_dic["hash"] = deck["deck_hash"]
                cards_dic["deck_name"] = l_deck_info["deck_name"]
                l_cards.append(cards_dic)
        return l_cards

    if request.method == "GET":

        learning_cards = learning_decks()

        algo_cards = []
        for card in learning_cards:
            for al_card in card["cards"]:
                algo_cards.append(al_card)

        algo_cards.sort(key=lambda algo_scores: int(algo_scores[3]))
        return dumps(algo_cards)

    elif request.method == "POST":
        practice_cards = request.get_data()
        practice_cards = loads(practice_cards)

        cards_update = learning_decks()

        # I could make this function more efficient, by updating x instead of making a new_cards variable
        new_scores = []
        for x in cards_update:
            new_cards = {"deck_name": x["deck_name"], "cards": []}
            for y in x["cards"]:
                new_cards["cards"].append(list(y))
            new_cards["hash"] = x["hash"]
            new_scores.append(new_cards)

        for pc in practice_cards:
            for card_dic in new_scores:
                for cards in card_dic["cards"]:
                    if cards[0] == pc[0]:
                        cards[3] = pc[3]

        with db.connect() as cur:
            stmt = sqlalchemy.text("UPDATE decks SET deck_info=:deck_info WHERE deck_hash=:deck_hash")
            for new in new_scores:
                word, definition, example, scores = map(list, zip(*new["cards"]))

                deck_info = {"deck_name": new["deck_name"], "word": word, "definition": definition, "example": example,
                             "scores": scores}

                cur.execute(stmt, parameters={"deck_info": dumps(deck_info), "deck_hash": new["hash"]})

            cur.commit()

        return "/"


@app.route("/feedback", methods=["POST", "GET"])
def feedback():
    if request.method == "POST":
        f_name = request.form.get("f-name")
        f_email = request.form.get("f-email")
        f_econtent = request.form.get("f-econtent")

        message = MIMEMultipart()
        message["Subject"] = "Literate Feedback"
        message["From"] = feedback_email
        message["To"] = feedback_email
        feedback_message = MIMEText(f"Name: {f_name}\n\nEmail: {f_email}\n\n{f_econtent}")
        message.attach(feedback_message)

        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.starttls()
            server.login(feedback_email, sender_pass)
            server.sendmail(feedback_email, feedback_email, message.as_string())
            return redirect("/")
    else:
        return render_template("/feedback.html")


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080, threads=2)
