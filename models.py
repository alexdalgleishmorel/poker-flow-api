import enum
from dataclasses import dataclass
import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer, Text, String, DateTime, Float, Boolean, Enum
from sqlalchemy.sql import func

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
class Pool(Base):

    __tablename__ = "pool"

    id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    pool_name = Column(String(255), nullable=False)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    last_modified = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    settings_id = Column(Integer, ForeignKey("poolsettings.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("profile.id"), nullable=False)
    total_pot = Column(Float, nullable=False, default=0)
    available_pot = Column(Float, nullable=False, default=0)

    def __repr__(self):
        return f"<Pool {self.id}>"

@dataclass
class PoolSettings(Base):

    __tablename__ = "poolsettings"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    min_buy_in = Column(Float, nullable=False)
    max_buy_in = Column(Float, nullable=False)
    denominations = Column(String(255), nullable=False)
    buy_in_enabled = Column(Boolean, nullable=False, default=True)
    expired = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Pool Setting {self.id}>"

@dataclass
class PoolMember(Base):

    __tablename__ = "poolmember"

    pool_id = Column(String(36), ForeignKey("pool.id"), primary_key=True, nullable=False)
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True, nullable=False)

    def __repr__(self):
        return f"<Pool {self.id}>"

@dataclass
class Transaction(Base):

    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    pool_id = Column(String(36), ForeignKey("pool.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profile.id"), nullable=False)
    date = Column(DateTime, nullable=False, server_default=func.now())
    type = Column(Enum(TransactionTypes), nullable=False)
    amount = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Transaction {self.id}>"
