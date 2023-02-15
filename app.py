from flask import Flask, session, redirect, request, render_template
from helpers import login_required
from flask_session import Session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

# /login -- Done
# /register -- Done

# /start_page
# /dashboard
# /practice
# /create_deck
# /find_decks

# last practice is how I will track streaks, no con login
# email have to be unique key
# check for email availability (instant)


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
    return render_template("dashboard.html")


@app.route("/start_page")
def start_page():
    return render_template("start_page.html")


@app.route("/login", methods=["POST", "GET"])
def login():

    session.clear()
    login_error = ""

    if request.method == "POST":
        cur.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"), ))
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
        email = request.form.get("email")

        cur.execute('INSERT INTO users (email, password_hash) VALUES(?, ?)',
                    (email, password_hash))
        conn.commit()

        cur.execute("SELECT id FROM users")
        return redirect("/login")
    else:
        return render_template("register.html")
