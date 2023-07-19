import bcrypt
from sqlalchemy import select

from models import Profile

class EmailAlreadyExistsException(Exception):
    pass

class EmailNotFoundException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

def create(session, data):
    # Verify if the email already exists within the database
    query = select(Profile).filter_by(email=data['email'])
    rows = session.execute(query).all()
    if rows:
        raise EmailAlreadyExistsException
    
    # Create the new profile
    profile = Profile(
        email = data['email'],
        firstName = data['firstName'],
        lastName = data['lastName'],
        hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt(rounds=12))
    )
    session.add(profile)
    session.commit()

def login(session, data):
    # Query the database for the given email
    query = select(Profile).filter_by(email=data['email'])
    result = session.execute(query).fetchone()
    if not result:
        raise EmailNotFoundException
    
    profile = result[0]
    
    # Verify the provided password
    if not bcrypt.checkpw(data['password'].encode('utf-8'), profile.hash.encode('utf-8')):
        raise InvalidPasswordException
    
    # Return the profile information
    return {
        'id': profile.id,
        'email': profile.email,
        'firstName': profile.firstName,
        'lastName': profile.lastName
    }

def get_user_first_last(id, session):
    query = select(Profile).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise UserNotFoundException
    
    profile = rows[0]

    return {
        "id": id,
        "firstName": profile.firstName,
        "lastName": profile.lastName
    }
