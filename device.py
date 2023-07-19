import database
from models import Device


def create():
    session = database.DatabaseConnector.get_session()

    try:
        # Create the new device
        device = Device()
        session.add(device)
        session.commit()

    finally:
        session.close()
