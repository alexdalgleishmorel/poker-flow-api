from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import constants

def get_engine():
    """
    Initializes a connection engine to the database using parameters defined in the 'constants' module. 
    Uses the MSSQL+pyodbc dialect for connecting to an MSSQL database.

    Returns:
    Engine: An SQLAlchemy Engine instance connected to the specified database.
    """
    return create_engine(url=f"mssql+pyodbc://{constants.USER}:{constants.PASSWORD}@{constants.HOST}:{constants.PORT}/{constants.DATABASE}?driver={constants.DRIVER}&{constants.TRUST}")

def get_session():
    """
    Initializes a scoped session using the SQLAlchemy sessionmaker, bound to the engine created by 'get_engine()'.

    Returns:
    Session: An SQLAlchemy session object for database operations.
    """
    Session = scoped_session(sessionmaker(bind=get_engine()))
    return Session()
