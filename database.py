from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, threadlocal

import constants

class DatabaseConnector:
    _engine = None
    _session = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._engine = create_engine(url=f"mssql+pyodbc://{constants.USER}:{constants.PASSWORD}@{constants.HOST}:{constants.PORT}/{constants.DATABASE}?driver={constants.DRIVER}&{constants.TRUST}")
        return cls._engine

    @classmethod
    def get_session(cls):
        if cls._session is None:
            Session = scoped_session(sessionmaker(bind=cls.get_engine()), scopefunc=threadlocal)
            cls._session = Session()
        return cls._session
