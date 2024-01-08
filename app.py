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
    Pings back a 200 response for health monitoring
    """
    return '', 200

@app.route('/game/active/user/<string:id>', methods=['GET'])
@with_session
def get_active_games_by_user_id(session, id):
    """
    Queries for active games associated with the given user ID
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
    Queries for expired games associated with the given user ID
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
    Queries for a game with the given game ID
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
    Creates a new game, based on the specifications supplied in the request body
    """
    data = request.get_json()
    created_game = game.create(session, data)
    return created_game, 201

@app.route('/game/settings/update', methods=['POST'])
@with_session
def update_game_settings(session):
    """
    Update game attributes
    """
    data = request.get_json()
    updated_game = game.update_settings(session, data)
    socketio.emit('game_updated', updated_game, room=updated_game['id'])
    return updated_game, 200

@app.route('/game/join', methods=['POST'])
@with_session
def join_game(session):
    """
    Adds the specified user as a member of the given game
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
    Creates a new transaction record
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
    data = request.get_json()
    try:
      user.create(session, data)
      return "", 201

    except EmailAlreadyExistsException:
      return "EmailAlreadyExists: A profile with the given email already exists within the database", 401
    
@app.route('/verifyUniqueEmail', methods=['POST'])
@with_session
def verifyUniqueEmail(session):
    data = request.get_json()
    try:
      user.verifyUniqueEmail(session, data)
      return "true", 200

    except EmailAlreadyExistsException:
      return "false", 200
    
@app.route('/updateUser', methods=['POST'])
@with_session
def updateUser(session):
    data = request.get_json()
    try:
      profile_data = user.updateUser(session, data)
      return { "jwt": auth.generate_jwt(profile_data) }

    except EmailAlreadyExistsException:
      return "EmailAlreadyExists: A profile with the given email already exists within the database", 401
    
@socketio.on('subscribe_to_game')
def on_subscribe_to_game(data):
    game_id = data['game_id']
    print(game_id)
    join_room(game_id)

@socketio.on('unsubscribe_from_game')
def on_unsubscribe_from_game(data):
    game_id = data['game_id']
    print(game_id)
    leave_room(game_id)
    
if __name__ == '__main__':
    socketio.run(app, host=API_HOST, port=API_PORT)
