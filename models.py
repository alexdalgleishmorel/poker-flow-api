import enum
from dataclasses import dataclass
import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Integer, Text, String, DateTime, Float, Boolean, Enum
from sqlalchemy.sql import func

def generate_uuid():
    return str(uuid.uuid4())

Base = declarative_base()

class TransactionTypes(str, enum.Enum):
    BUY_IN = "BUY_IN"
    CASH_OUT = "CASH_OUT"
    BET = "BET"

@dataclass
class Profile(Base):

    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    email:str = Column(String(320), unique=True, nullable=False)
    firstName:str = Column(String(255), nullable=False)
    lastName:str = Column(String(255), nullable=False)
    hash = Column(Text, nullable=False)

@dataclass
class Game(Base):

    __tablename__ = "game"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    last_modified = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    settings_id = Column(Integer, ForeignKey("gamesettings.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("profile.id"), nullable=False)
    _total_pot = Column(Float, nullable=False, default=0)
    _available_cashout = Column(Float, nullable=False, default=0)

    @hybrid_property
    def total_pot(self):
        return self._total_pot

    @total_pot.setter
    def total_pot(self, value):
        self._total_pot = round(value, 2)

    @hybrid_property
    def available_cashout(self):
        return self._available_cashout

    @available_cashout.setter
    def available_cashout(self, value):
        self._available_cashout = round(value, 2)

    def __repr__(self):
        return f"<Game {self.id}>"

@dataclass
class GameSettings(Base):

    __tablename__ = "gamesettings"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    _min_buy_in = Column(Float, nullable=False)
    _max_buy_in = Column(Float, nullable=False)
    denominations = Column(String(255), nullable=False)
    denomination_colors = Column(String(255), nullable=False)
    buy_in_enabled = Column(Boolean, nullable=False, default=True)
    expired = Column(Boolean, nullable=False, default=False)

    @hybrid_property
    def min_buy_in(self):
        return self._min_buy_in

    @min_buy_in.setter
    def min_buy_in(self, value):
        self._min_buy_in = round(value, 2)

    @hybrid_property
    def max_buy_in(self):
        return self._max_buy_in

    @max_buy_in.setter
    def max_buy_in(self, value):
        self._max_buy_in = round(value, 2)

    def __repr__(self):
        return f"<Game Setting {self.id}>"

@dataclass
class GameMember(Base):

    __tablename__ = "gamemember"

    game_id = Column(String(36), ForeignKey("game.id"), primary_key=True, nullable=False)
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True, nullable=False)

    def __repr__(self):
        return f"<Game {self.id}>"

@dataclass
class Transaction(Base):

    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    game_id = Column(String(36), ForeignKey("game.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profile.id"), nullable=False)
    date = Column(DateTime, nullable=False, server_default=func.now())
    type = Column(Enum(TransactionTypes), nullable=False)
    _amount = Column(Float, nullable=False)
    denominations = Column(String(255), nullable=False)

    @hybrid_property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = round(value, 2)

    def __repr__(self):
        return f"<Transaction {self.id}>"
