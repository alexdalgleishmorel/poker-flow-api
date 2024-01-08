import flask
from flask import request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
from sqlalchemy.exc import SQLAlchemyError

import auth
from constants import API_HOST, API_PORT, CLIENT_HOST, CLIENT_PORT
import database
import game
from game import GameNotFoundException, InvalidPasswordException as InvalidGamePasswordException, InvalidTransactionException
import user
from user import EmailAlreadyExistsException, EmailNotFoundException, InvalidPasswordException as InvalidUserPasswordException

app = flask.Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins=f"http://{CLIENT_HOST}:{CLIENT_PORT}")
cors = CORS(app)

def with_session(func):
    def wrapper(*args, **kwargs):
        session = database.get_session()
        try:
            return func(session, *args, **kwargs)
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    # Assign a unique name to the wrapper function based on the original function name
    wrapper.__name__ = func.__name__ + '_with_session'
    return wrapper

@app.route('/', methods=['GET', 'POST'])
def health_check():
    """
    Endpoint for health check of the application.

    Responds with a 200 status code to indicate that the application is running properly. 

    Methods:
    GET, POST
    """
    return '', 200

@app.route('/game/active/user/<string:id>', methods=['GET'])
@with_session
def get_active_games_by_user_id(session, id):
    """
    Retrieves active games where the specified user is a member. Supports pagination.

    Methods:
    GET

    URL Parameters:
    id (str): The user ID for which active games are being queried.
    itemOffset (int): Query parameter for pagination offset.
    itemsPerPage (int): Query parameter for number of items per page.

    Returns:
    JSON response containing a list of active games associated with the user.
    """
    try:
        games = game.get_by_user_id(
            session, 
            id, 
            itemOffset=request.args.get('itemOffset', type=int), 
            per_page=request.args.get('itemsPerPage', type=int),
            expired=False
        )
        return jsonify(games)
    except GameNotFoundException:
        return "GameNotFound: No games found relating to the specified user ID", 404
    
@app.route('/game/expired/user/<string:id>', methods=['GET'])
@with_session
def get_expired_games_by_user_id(session, id):
    """
    Retrieves expired games where the specified user is a member. Supports pagination.

    Methods:
    GET

    URL Parameters:
    id (str): The user ID for which active games are being queried.
    itemOffset (int): Query parameter for pagination offset.
    itemsPerPage (int): Query parameter for number of items per page.

    Returns:
    JSON response containing a list of active games associated with the user.
    """
    try:
        games = game.get_by_user_id(
            session, 
            id, 
            itemOffset=request.args.get('itemOffset', type=int), 
            per_page=request.args.get('itemsPerPage', type=int),
            expired=True
        )
        return jsonify(games)
    except GameNotFoundException:
        return "GameNotFound: No games found relating to the specified user ID", 404

@app.route('/game/<string:id>', methods=['GET'])
@with_session
def get_game_by_id(session, id):
    """
    Retrieves comprehensive information about a game, identified by its unique ID.

    Methods:
    GET

    URL Parameters:
    id (str): The unique identifier of the game to retrieve.

    Returns:
    JSON response with game data if found.
    """
    try:
      game_data = game.get_by_id(session, id)
      return jsonify(game_data)
    except GameNotFoundException:
      return "GameNotFound: No game found with the specified ID", 404


@app.route('/game/create', methods=['POST'])
@with_session
def create_game(session):
    """
    Creates a new game based on specifications provided in the request body. 
    Commits the game and its settings to the database.

    Methods:
    POST

    Request Body:
    JSON containing the specifications for the new game.

    Returns:
    JSON response containing the newly created game data.
    """
    data = request.get_json()
    created_game = game.create(session, data)
    return created_game, 201

@app.route('/game/settings/update', methods=['POST'])
@with_session
def update_game_settings(session):
    """
    Updates attributes of a game's settings. The updates are specified in the request body. 
    Upon successful update, a 'game_updated' event is emitted to all subscribers of the game room via SocketIO.

    Methods:
    POST

    Request Body:
    JSON containing the game ID and a list of update requests for the game settings.

    Returns:
    JSON response with the updated game data.
    """
    data = request.get_json()
    updated_game = game.update_settings(session, data)
    socketio.emit('game_updated', updated_game, room=updated_game['id'])
    return updated_game, 200

@app.route('/game/join', methods=['POST'])
@with_session
def join_game(session):
    """
    Adds the specified user as a member of a given game. 
    Details of the user and the game are provided in the request body.

    Methods:
    POST

    Request Body:
    JSON containing the user ID and game ID.

    Returns:
    An empty response with a 201 status code upon success.
    """
    data = request.get_json()
    try:
      game.join(session, data)
      return "", 201
    
    except GameNotFoundException:
        return "Game Not Found: The given game ID could not be found", 404
    except InvalidGamePasswordException:
        return "Invalid Credentials: The supplied game password is incorrect", 401
        

@app.route('/game/transaction/create', methods=['POST'])
@with_session
def create_transaction(session):
    """
    Handles the creation of transactions within a game. 
    The transaction details are provided in the request body. 
    Upon successful creation, a 'game_updated' event is emitted to all subscribers of the game room via SocketIO.

    Methods:
    POST

    Request Body:
    JSON containing transaction details such as game ID, amount, and type.

    Returns:
    JSON response with the transaction amount and type.
    """
    data = request.get_json()
    try:
        amount, type = game.create_transaction(session, data)
        updated_game = game.get_by_id(session, data['gameID'])
        socketio.emit('game_updated', updated_game, room=updated_game['id'])
        return { 'amount': amount, 'type': type }, 201
    except InvalidTransactionException:
        return "Invalid Transaction Error: The provided transaction was invalid", 400


@app.route('/login', methods=['POST'])
@with_session
def login(session):
    """
    Authenticates a user based on their email and password. 
    On successful authentication, a JSON Web Token (JWT) is generated and returned.

    Methods:
    POST

    Request Body:
    JSON containing the user's email and password.

    Returns:
    JSON response with a generated JWT for the authenticated user.
    """
    data = request.get_json()
    try:
      profile_data = user.login(session, data)
      return { "jwt": auth.generate_jwt(profile_data) }

    except EmailNotFoundException:
        return "EmailNotFound: No profile with the given email could be found", 404
    except InvalidUserPasswordException:
        return "Invalid Credentials: The supplied username and password are invalid", 401

@app.route('/signup', methods=['POST'])
@with_session
def signup(session):
    """
    Registers a new user in the database. The user's details are provided in the request body.
    If the email already exists in the database, an exception is raised.

    Methods:
    POST

    Request Body:
    JSON containing the new user's profile information.

    Returns:
    An empty response with a 201 status code upon successful registration.
    """
    data = request.get_json()
    try:
      user.create(session, data)
      return "", 201

    except EmailAlreadyExistsException:
      return "EmailAlreadyExists: A profile with the given email already exists within the database", 401
    
@app.route('/verifyUniqueEmail', methods=['POST'])
@with_session
def verifyUniqueEmail(session):
    """
    Verifies whether the provided email in the request body already exists in the database.

    Methods:
    POST

    Request Body:
    JSON containing the email to verify.

    Returns:
    A response with "true" or "false" based on the uniqueness of the email.
    """
    data = request.get_json()
    try:
      user.verifyUniqueEmail(session, data)
      return "true", 200

    except EmailAlreadyExistsException:
      return "false", 200
    
@app.route('/updateUser', methods=['POST'])
@with_session
def updateUser(session):
    """
    Allows a user to update their profile details like first name, last name, and email. 
    The updated information is provided in the request body. 
    A new JWT is generated and returned after the update.

    Methods:
    POST

    Request Body:
    JSON containing the user's updated profile information.

    Returns:
    JSON response with a new JWT for the updated profile.
    """
    data = request.get_json()
    try:
      profile_data = user.updateUser(session, data)
      return { "jwt": auth.generate_jwt(profile_data) }

    except EmailAlreadyExistsException:
      return "EmailAlreadyExists: A profile with the given email already exists within the database", 401
    
@socketio.on('subscribe_to_game')
def on_subscribe_to_game(data):
    """
    SocketIO event for subscribing to game updates.

    When a client connects to this SocketIO event with a game ID, 
    they are added to a room specific to that game to receive real-time updates.

    Parameters:
    data (dict): Data containing the 'game_id' key to specify which game room to join.
    """
    game_id = data['game_id']
    print(game_id)
    join_room(game_id)

@socketio.on('unsubscribe_from_game')
def on_unsubscribe_from_game(data):
    """
    SocketIO event for unsubscribing from game updates.

    Allows a client to leave a specific game room, ceasing to receive real-time updates about that game.

    Parameters:
    data (dict): Data containing the 'game_id' key to specify which game room to leave.
    """
    game_id = data['game_id']
    print(game_id)
    leave_room(game_id)
    
if __name__ == '__main__':
    socketio.run(app, host=API_HOST, port=API_PORT)
