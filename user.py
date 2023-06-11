from sqlalchemy import select

import database
from models import Profile

class EmailAlreadyExistsException(Exception):
    pass

def create(data):

    session = database.get_session()

    try:
        # Verify if the email already exists within the database
        query = select(Profile).filter_by(email=data['email'])
        rows = session.execute(query).all()
        if (rows):
            raise EmailAlreadyExistsException
        
        # Create the new profile
        profile = Profile(
            email = data['email'],
            firstName = data['firstName'],
            lastName = data['lastName'],
            hash = data['hash'],
            salt = data['salt']
        )
        session.add(profile)
        session.commit()
        return profile

    finally:
        session.close()
