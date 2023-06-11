from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import constants

def get_engine():
    return create_engine(url=f"mssql+pyodbc://{constants.USER}:{constants.PASSWORD}@{constants.HOST}:{constants.PORT}/{constants.DATABASE}?driver={constants.DRIVER}&{constants.TRUST}")

def get_session():
    Session = sessionmaker(bind=get_engine())
    return Session()
