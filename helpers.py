from functools import wraps
from flask import redirect, session
import inflect


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/start_page")
        return f(*args, **kwargs)
    return decorated_function


def generate_unique_id(id_number):
    hasher = inflect.engine()
    word = hasher.number_to_words(id_number)

    if id_number % 10 in [0, 3, 7, 8]:
        return_hash = 'uwx'
    elif id_number % 10 in [1, 4, 5, 9]:
        return_hash = 'vxy'
    else:
        return_hash = 'wyz'

    for counter, ch in enumerate(word):
        if ord(ch) == ord(" "):
            continue
        if counter % 2 == 0:
            return_hash += ch
        else:
            return_hash += str(ord(ch))
    return return_hash
