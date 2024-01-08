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

def updateUser(session, data):
    """
    Updates a user profile based on the provided data.

    Parameters:
    session (Session): The database session to use for the update.
    data (dict): A dictionary containing the user's ID and the new profile information (first name, last name, and email).

    Returns:
    dict: A dictionary containing the updated profile information.

    Raises:
    UserNotFoundException: If no user is found with the provided ID.
    """
    query = select(Profile).filter_by(id=data['id'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise UserNotFoundException
    
    profile = rows[0]

    profile.firstName = data['firstName']
    profile.lastName = data['lastName']
    profile.email = data['email']
    
    session.commit()

    # Return the profile information
    return {
        'id': profile.id,
        'email': profile.email,
        'firstName': profile.firstName,
        'lastName': profile.lastName
    }

def verifyUniqueEmail(session, data):
    """
    Verifies if the provided email address already exists in the database. If it does, it raises an EmailAlreadyExistsException.

    Parameters:
    session (Session): The database session for the query.
    data (dict): A dictionary containing the email address to be verified.

    Returns:
    bool: True if the email is unique, otherwise raises an exception.

    Raises:
    EmailAlreadyExistsException: If the provided email already exists in the database.
    """
    # Verify if the email already exists within the database
    query = select(Profile).filter_by(email=data['email'])
    rows = session.execute(query).all()
    if rows:
        raise EmailAlreadyExistsException
    else:
        return True

def create(session, data):
    """
    Creates a new user profile in the database.

    This function first checks for the uniqueness of the provided email address. If the email is unique, it creates a new profile with the provided information, hashing the password for security.

    Parameters:
    session (Session): The database session to be used for creating the profile.
    data (dict): A dictionary containing the user's profile information (email, first name, last name, and password).

    Raises:
    EmailAlreadyExistsException: If the provided email already exists in the database.
    """
    verifyUniqueEmail(session, data)
    
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
    """
    Authenticates a user based on email and password.
    If authentication is successful, it returns the user's profile information.

    Parameters:
    session (Session): The database session for the query.
    data (dict): A dictionary containing the user's email and password.

    Returns:
    dict: A dictionary containing the user's profile information if authentication is successful.

    Raises:
    EmailNotFoundException: If no user is found with the provided email.
    InvalidPasswordException: If the provided password does not match the stored hash.
    """
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
    """
    Retrieves a user's profile using their unique ID. 
    If found, it returns their first and last name.

    Parameters:
    id (int): The unique identifier of the user.
    session (Session): The database session for the query.

    Returns:
    dict: A dictionary containing the user's first and last name.

    Raises:
    UserNotFoundException: If no user is found with the provided ID.
    """
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
