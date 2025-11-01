# Server
from flask import Flask, session, redirect, request, render_template, jsonify
from flask_session import Session
from flask_cors import CORS
# from waitress import serve

# Functions
from werkzeug.security import check_password_hash, generate_password_hash
from literateApp.helpers import login_required, generate_unique_id

# Database
import sqlalchemy
from literateApp.sqlalchemy_helpers import return_dict, sqlalchemy_db_init
from sqlalchemy.orm import sessionmaker
from literateApp.models import Deck, User, Base

# Data
from json import loads, dumps

# Emails
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Error handling
from sqlalchemy.exc import IntegrityError
import os

# Email config
feedback_email = "literate22@outlook.com"
sender_pass = "nefpy0-wycdEj-mocrid"

# Configure application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "9f2b58b1785dl1poA89shecb0e23967a4ce81460f179e4c5c3a17d3a41b32b8e")
CORS(app)
# app.debug = True

# Configure session to use filesystem instead of signed cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "null"
Session(app)

# Connect to database
# Refactoring needed
db = sqlalchemy_db_init(
    driver_name="postgresql+psycopg2",
    user="avnadmin",
    password=os.getenv("DBPASS"),
    host="literate-diegowork2203-947d.c.aivencloud.com",
    port=20560,
    db_name="defaultdb",
)

sqlalchemy_Session = sessionmaker(bind=db)
Base.metadata.create_all(bind=db)


@login_required
def parse_deck_info(user_id, access=None):
    with sqlalchemy_Session() as sqlalchemy_session:
        if user_id and not access:
            decks = return_dict(sqlalchemy_session.query(Deck).filter(Deck.user_id == user_id))
        elif access == "Public" and user_id:
            decks = return_dict(sqlalchemy_session.query(Deck).filter(Deck.user_id != user_id).filter(Deck.access == access))

    decks_list = []
    for d in decks:
        deck_info = loads(d["deck_info"])
        x = {"deck_name": d["deck_name"], "word_count": len(deck_info["word"]),
             "deck_hash": d["deck_hash"], "user_id": d["user_id"], "learning": d["learning"]}
        decks_list.append(x)
    return decks_list


@login_required
def render_stats():
    user_id = session["user_id"]
    with sqlalchemy_Session() as sqlalchemy_session:
        decks = sqlalchemy_session.query(Deck.deck_info).filter(Deck.user_id == user_id)

        word_count = 0
        words_mastered = 0

        for d in decks:
            deck_info = loads(d[0])
            word_count += len(deck_info["word"])

            # To make words_mastered show the mastered words, I need enumerate,
            # because I will have to access deck_info["word"][i]
            for i, score in enumerate(deck_info["scores"]):
                if int(score) >= 15:
                    words_mastered += 1

    return word_count, words_mastered


# Refactoring (SQL)
@login_required
def paand(user_id: int, action: str, deck_hash: str = None, access: str = None, info: dict = None, add: str = None):
    def community_share_check(deck_info_community_share) -> str:
        try:
            del deck_info['save-changes']
        except KeyError:
            pass
        try:  # community-share does not need to be refactored, this is the only place I use it, it comes from the
            # html and js, where the slider for sharing has id or name community-share
            if deck_info_community_share["community-share"][0] == "on":
                del deck_info["community-share"]
                return "Public"
            elif deck_info_community_share["community-share"][0] == "Private":
                del deck_info["community-share"]
                return "Private"
        except KeyError:
            return "Private"

    with sqlalchemy_Session() as sqlalchemy_session:
        if deck_hash:

            deck: list= return_dict(sqlalchemy_session.query(Deck).filter(Deck.deck_hash == deck_hash))
            owner_id = deck[0]["user_id"]
            if owner_id == user_id:
                scores: list = loads(deck[0]["deck_info"])['scores']
                deck_info = request.form.to_dict(flat=False)
                deck_info["scores"]: list = scores
                if len(deck_info["scores"]) != len(deck_info["word"]):
                    deck_info["scores"] += ["0"]*(len(deck_info["word"])-len(deck_info["scores"]))
            else:
                if add == "add":
                    deck_info = request.form.to_dict(flat=False)
                    pass
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

        if action == "insert":
            new_deck_obj = Deck(user_id=user_id, deck_name=deck_info["deck_name"][0], deck_info=dumps(deck_info),
                                access=access)
            sqlalchemy_session.add(new_deck_obj)
            sqlalchemy_session.flush()
            sqlalchemy_session.query(Deck).filter(Deck.deck_id == new_deck_obj.deck_id).update(
                {"deck_hash": generate_unique_id(new_deck_obj.deck_id)})

            sqlalchemy_session.commit()
            return 0

        # maybe deck_name[0] -> deck_name
        elif action == "update" and owner_id == user_id:
            sqlalchemy_session.query(Deck).filter(Deck.user_id == user_id, Deck.deck_hash == deck_hash).update(
                {"deck_name": deck_info["deck_name"][0], "deck_info": dumps(deck_info), "access": access})
            sqlalchemy_session.commit()
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
            return redirect("/")
        else:
            return inserted

    else:
        return render_template("/index.html", decks_list=parse_deck_info(user_id), stats=render_stats())


@app.route("/start_page")
def start_page():
    return render_template("/start_page.html")


@app.route("/login", methods=["POST", "GET"])
def login():

    session.clear()
    login_error = "Invalid email or password."

    if request.method == "POST":
        with sqlalchemy_Session() as sqlalchemy_session:
            email = request.form.get("email").lower()
            user = return_dict(sqlalchemy_session.query(User).filter(User.email == email))
        try:
            if user[0]['email'] and check_password_hash(user[0]['password_hash'], request.form.get("password")):
                session["user_id"] = user[0]["user_id"]
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

        with sqlalchemy_Session() as sqlalchemy_session:
            try:
                sqlalchemy_session.add(User(email, password_hash))
                sqlalchemy_session.commit()
            except sqlalchemy.exc.IntegrityError:
                return render_template("/register")

            session["user_id"] = sqlalchemy_session.query(User.user_id).filter(User.email == email)[0][0]
        return redirect("/")

    else:
        return render_template("/register.html")


@app.route("/email_availability", methods=["POST"])
def email_availability():
    if request.method == "POST":
        availability = False
        with sqlalchemy_Session() as sqlalchemy_session:
            try:
                sqlalchemy_session.query(User.email).filter(User.email == request.form.get("email").lower())[0]
            except IndexError:
                availability = True
        return jsonify({"available": availability})


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

        paand(user_id, "update", deck_hash=deck_hash, add="add")
        return redirect("/")
    else:
        with sqlalchemy_Session() as sqlalchemy_session:
            deck = return_dict(sqlalchemy_session.query(Deck).filter(Deck.deck_hash == deck_hash))

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
        with sqlalchemy_Session() as sqlalchemy_session:
            try:
                owner_id = sqlalchemy_session.query(Deck.user_id).filter(Deck.deck_hash == deck_hash)[0][0]
            except TypeError:
                pass

            if owner_id == user_id:
                sqlalchemy_session.query(Deck).filter(Deck.deck_hash == deck_hash).delete()
                sqlalchemy_session.commit()
        return redirect("/")


@app.route("/find_decks", methods=["POST", "GET"])
@login_required
def find_other_decks():
    if request.method == "GET":
        user_id = session["user_id"]
        return render_template("/find_other_decks.html", decks_list=parse_deck_info(user_id, access="Public"))


@app.route("/save_other", methods=["POST", "GET"])
@login_required
def save_other():
    if request.method == "POST":
        user_id = session["user_id"]
        deck_hash = request.form.get("dsh")
        insert = paand(user_id, "update", deck_hash=deck_hash, access="Private")
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
        with sqlalchemy_Session() as sqlalchemy_session:
            sqlalchemy_session.query(Deck).filter(Deck.deck_hash == deck_hash).update({"learning": state})
            sqlalchemy_session.commit()
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

    def learning_decks(u_id):
        with sqlalchemy_Session() as l_ss:
            decks = l_ss.query(Deck.deck_info, Deck.deck_hash).filter(Deck.user_id == u_id, Deck.learning == "On")

        l_cards = []
        if decks:
            for deck in decks:
                cards_dic = {}
                l_deck_info = loads(deck[0])
                cards_dic["cards"] = (list(zip(l_deck_info["word"], l_deck_info["definition"], l_deck_info["example"],
                                           l_deck_info["scores"])))
                cards_dic["hash"] = deck[1]
                cards_dic["deck_name"] = l_deck_info["deck_name"]
                l_cards.append(cards_dic)
        return l_cards

    if request.method == "GET":

        learning_cards = learning_decks(user_id)

        algo_cards = []
        for card in learning_cards:
            for al_card in card["cards"]:
                algo_cards.append(al_card)

        algo_cards.sort(key=lambda algo_scores: int(algo_scores[3]))
        return dumps(algo_cards)

    elif request.method == "POST":
        practice_cards = request.get_data()
        practice_cards = loads(practice_cards)

        cards_update = learning_decks(user_id)

        # I could make this function more efficient, by updating x instead of making a new_cards variable
        # It bothers me how much I feel I can improve this function (and the one below)
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

        with sqlalchemy_Session() as sqlalchemy_session:
            for new in new_scores:
                word, definition, example, scores = map(list, zip(*new["cards"]))

                deck_info = {"deck_name": new["deck_name"], "word": word, "definition": definition, "example": example,
                             "scores": scores}
                sqlalchemy_session.query(Deck).filter(Deck.deck_hash == new["hash"]).update({
                    "deck_info": dumps(deck_info)})

            sqlalchemy_session.commit()

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


@app.route("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    # serve(app, host="127.0.0.1", port=8080, threads=2)
    app.run()
