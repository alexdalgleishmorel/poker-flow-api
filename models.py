import enum
from dataclasses import dataclass
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer, Text, String, DateTime, Float, Boolean, Enum
from sqlalchemy.sql import func

Base = declarative_base()

class TransactionTypes(enum.Enum):
    BUY_IN = "BUY_IN"
    CASH_OUT = "CASH_OUT"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

@dataclass
class Profile(Base):

    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    email:str = Column(String(320), unique=True, nullable=False)
    firstName:str = Column(String(255), nullable=False)
    lastName:str = Column(String(255), nullable=False)
    hash = Column(Text, nullable=False)

@dataclass
class PoolSettings(Base):

    __tablename__ = "poolsettings"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    min_buy_in = Column(Float, nullable=False)
    max_buy_in = Column(Float, nullable=False)
    denominations = Column(String(255), nullable=False)
    has_password = Column(Boolean, nullable=False)
    hash = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Pool Setting {self.id}>"

@dataclass
class Device(Base):

    __tablename__ = "device"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)

    def __repr__(self):
        return f"<Device {self.id}>"

@dataclass
class Pool(Base):

    __tablename__ = "pool"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    pool_name = Column(String(255), nullable=False)
    date_created = Column(DateTime, nullable=False, server_default=func.now())
    settings_id = Column(Integer, ForeignKey("poolsettings.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("profile.id"), nullable=False)

    def __repr__(self):
        return f"<Pool {self.id}>"

@dataclass
class Transaction(Base):

    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement='auto', nullable=False)
    pool_id = Column(Integer, ForeignKey("pool.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    date = Column(DateTime, nullable=False, server_default=func.now())
    type = Column(Enum(TransactionTypes), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.id}>"
