import psycopg2
import sqlalchemy.exc
from sqlalchemy.orm import sessionmaker
from literateApp.models import User, Deck
from literateApp.helpers import generate_unique_id
from literateApp.sqlalchemy_helpers import return_dict, sqlalchemy_db_init

from functools import wraps

from werkzeug.security import check_password_hash, generate_password_hash
from json import loads, dumps


import sqlite3
sqlite_db = sqlite3.connect("../literate.sqlite")
sqlite_db.row_factory = sqlite3.Row
sqlite_cur = sqlite_db.cursor()


def function_timer(f):
    from time import perf_counter

    @wraps(f)
    def decorator_function(*args, **kwargs):
        start_time = perf_counter()
        function = f(*args, **kwargs)
        end_time = perf_counter()
        print(f"{f.__name__}({args} {kwargs})-- {end_time-start_time}")
        return function
    return decorator_function


postgresql_db = sqlalchemy_db_init(driver_name="postgresql+psycopg2", user="root",
                                   password="rQ6Qp26tW2UWfl9kgtMZdWeB2vzNee1N",
                                   host="dpg-ch5u8omkobid0i2silvg-a.oregon-postgres.render.com", port=5432,
                                   db_name="postgresql_testing")

sqlalchemy_Session = sessionmaker(bind=postgresql_db)
