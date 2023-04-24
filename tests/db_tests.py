# import sqlite3

from literateApp.app import paand
import sqlalchemy
from werkzeug.security import check_password_hash, generate_password_hash
from json import loads, dumps
from literateApp.helpers import generate_unique_id


# sqlite_conn = sqlite3.connect("../literate.sqlite")
# sqlite_conn.row_factory = sqlite3.Row
# sqlite_cur = sqlite_conn.cursor()


def init_db():
    db_user = "root"
    db_pass = "Prien-21."
    db_name = "mysql-testing"
    db_host = "localhost"
    db_port = 3306
    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
        ),
        pool_size=5,
        max_overflow=2,
        pool_timeout=60,
        pool_recycle=1800,
    )
    return pool


testing_db = init_db()


def select_test():
    x = [{'deck_id': 1, 'user_id': 4, 'deck_info': '{"deck_name": ["Going to the restaurant"], "word": ["Abendessen", "am beliebtesten", "das Fr\\u00fchst\\u00fcck", "das Restaurant", "der Tisch", "die Rechnung", "die Speisekarte", "empfehlen", "hungrig", "Ich m\\u00f6chte __", "K\\u00f6nnen wir warten?", "lassen", "Mittagessen", "Nichts f\\u00fcr mich", "Reservierung", "Stimmt so", "vegetarisch", "Wann bist du offen?"], "definition": ["dinner", "Most popular", "Breakfast", "Restaurant", "table", "bill", "menu", "recommend", "hungry", "I would like __", "Can we wait?", "to let, allow , have done", "Lunch", "Nothing for me", "reservation", "Keep the change", "vegetariann", "When are you open?"], "example": ["Wann ist Abendessen heute nacht? (When is dinner tonight?)", "Was ist das beliebteste Gericht? (What is the most popular dish?)", "Um acht Uhr gibt es Fr\\u00fchst\\u00fcck. (Breakfast is a t 8 o\'clock.)", "Was restaurant empfehlen Sie? (What restaurant do you recommend?)", "Ein Tisch f\\u00fcr drei Personen bitte. (A table for three people please.)", "Entschuldigung, die Rechnung bitte. (Excuse me, the bill please)", "K\\u00f6nnten Sie uns noch eine Speisekarte bringen? (Could you bring another menu?)", "K\\u00f6nnen Sie etwas empfehlen? (Can you recommend something?)", "Ich bin hungrig. Lass geht zu die pizza restaurant. (I am hungry. Let\'s go to the pizza restaurant.)", "Ich m\\u00f6chte Wiener Schnitzel mit Pommes bitte. (I want a Vienna style schnitzel with fries please.)", "K\\u00f6nner wir warten auf ein Tisch? (Can we wait for a table?)", "Lass uns zu Mittagessen. (Leg\'s have lunch.)", "Wo sollen wir zu Mittagessen? (Where should we have lunch?)", "Nichts f\\u00fcr mich, danke. (Nothing for me, thank you.)", "Wir m\\u00f6chten einen Tisch f\\u00fcr vier Personen um sechzehn Uhr reservieren bitte. (We want to reserve a table for fort people at 5 o\'clock please.)", "", "Haben Sie irgendetwas vegetarisches oder veganisches? (Do you have anything vegetarian or vegan?)", "Bist du offen Montag um sieben Uhr? (Are you open Monday at 7?)"], "scores": ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"]}', 'deck_name': 'Going to the restaurant', 'access': 'Public', 'deck_hash': 'vxyo110e915la11b', 'learning': 'Off'}]
    print(loads(x[0]['deck_info'])['scores'])


select_test()


# def transfer(dbs):
#     sqlite_cur.execute("SELECT * FROM users")
#     sqlite_users = sqlite_cur.fetchall()
#     stmt = sqlalchemy.text("INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)")
#     with dbs.connect() as cur:
#         for sqlite_user in sqlite_users:
#             cur.execute(stmt, parameters={"email": sqlite_user['email'], "password_hash":
#             sqlite_user['password_hash']})
#         cur.commit()


# transfer(testing_db)


def paand_test(dbs, user_id, action, deck_hash=None, access=None, info=None, add=None):
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

        if action == "insert":
            insert_stmt = sqlalchemy.text("INSERT INTO decks (user_id, deck_name, deck_info, access) "
                                          "VALUES (:user_id, :deck_name, :deck_info, :access)")
            params = {"user_id": user_id, "deck_name": deck_info["deck_name"][0], "deck_info": dumps(deck_info), "access": access}

            cur.execute(insert_stmt, params)

            deck_id = cur.execute(sqlalchemy.text("SELECT LAST_INSERT_ID()")).fetchone()

            cur.execute(sqlalchemy.text("UPDATE decks SET deck_hash=:deck_hash WHERE deck_id=:deck_id"),
                        parameters={"deck_hash": generate_unique_id(deck_id), "deck_id": deck_id[0]})
            cur.commit()
            return 0

        elif action == "update" and owner_id == user_id:
            cur.execute(sqlalchemy.text("UPDATE decks SET deck_name=:deck_name, deck_info=:deck_info, access=:access "
                                        "WHERE user_id=:user_id AND deck_hash=:deck_hash"),
                        parameters={"deck_name": deck_info["deck_name"][0], "deck_info": dumps(deck_info),
                                    "access": access, "user_id": user_id, "deck_hash": deck_hash})
            cur.commit()
            return 0
        elif action == "update" and owner_id != user_id:
            deck_info["community-share"] = [access]
            paand(user_id, "insert", access="Private", info=deck_info)
            return 0
        else:
            return "Invalid action"
