from sqlalchemy import Column, Integer, VARCHAR, TEXT, ForeignKey
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column("user_id", Integer, primary_key=True, autoincrement=True)
    email = Column("email", VARCHAR(255), unique=True)
    password_hash = Column("password_hash", TEXT)

    def __init__(self, email, password_hash, user_id=None):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash

    def __repr__(self):
        return {"user_id": self.user_id, "email": self.email, "password_hash": self.password_hash}


class Deck(Base):
    __tablename__ = "decks"

    deck_id = Column("deck_id", Integer, primary_key=True, autoincrement=True)
    user_id = Column("user_id", Integer, ForeignKey("users.user_id"))
    deck_info = Column("deck_info", TEXT)
    deck_name = Column("deck_name", VARCHAR(255))
    access = Column("access", VARCHAR(255))
    deck_hash = Column("deck_hash", VARCHAR(255), unique=True)
    learning = Column("learning", VARCHAR(5))

    def __init__(self, deck_id, user_id, deck_info, deck_name, access, deck_hash, learning):
        self.deck_id = deck_id
        self.user_id = user_id
        self.deck_info = deck_info
        self.deck_name = deck_name
        self.access = access
        self.deck_hash = deck_hash
        self.learning = learning

    def __repr__(self):
        return {"deck_id": self.deck_id, "user_id": self.user_id, "deck_info": self.deck_info,
                "deck_name": self.deck_name, "access": self.access, "deck_hash": self.deck_hash,
                "learning": self.learning}
