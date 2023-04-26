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


# Hash update u_id == o_id add

def paand_test(dbs, user_id, action, deck_hash=None, access=None, info=None, add=None):

    with dbs.connect() as cur:
        deck = cur.execute(sqlalchemy.text("SELECT * FROM decks WHERE deck_hash=:deck_hash"),
                           parameters={"deck_hash": deck_hash}).mappings().all()

        owner_id = deck[0]["user_id"]

        scores = loads(deck[0]["deck_info"])['scores']

        deck_info = {}
        deck_info["scores"] = scores
        if len(deck_info["scores"]) != len(deck_info["word"]):
            deck_info["scores"] += ["0"]*(len(deck_info["word"])-len(deck_info["scores"]))

        deck_info["scores"] = ["0"]*len(deck_info["word"])

        cur.execute(sqlalchemy.text("UPDATE decks SET deck_name=:deck_name, deck_info=:deck_info, access=:access "
                                    "WHERE user_id=:user_id AND deck_hash=:deck_hash"),
                    parameters={"deck_name": deck_info["deck_name"][0], "deck_info": dumps(deck_info),
                                "access": access, "user_id": user_id, "deck_hash": deck_hash})
        cur.commit()
        return 0
