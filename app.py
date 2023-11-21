import flask
from flask import request, jsonify
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

import auth
import database
import pool
from pool import PoolNotFoundException, InvalidPasswordException as InvalidPoolPasswordException, InvalidTransactionException
import user
from user import EmailAlreadyExistsException, EmailNotFoundException, InvalidPasswordException as InvalidUserPasswordException

app = flask.Flask(__name__)
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

@app.route('/pool/user/<string:id>', methods=['GET'])
@with_session
def get_pools_by_user_id(session, id):
    """
    Queries for pools associated with the given user ID
    """
    try:
        pools = pool.get_by_user_id(
            session, 
            id, 
            itemOffset=request.args.get('itemOffset', type=int), 
            per_page=request.args.get('itemsPerPage', type=int)
        )
        return jsonify(pools)
    except PoolNotFoundException:
        return "PoolNotFound: No pools found relating to the specified user ID", 404


@app.route('/pool/<string:id>', methods=['GET'])
@with_session
def get_pool_by_id(session, id):
    """
    Queries for a pool with the given pool ID
    """
    try:
      pool_data = pool.get_by_id(session, id)
      return jsonify(pool_data)
    except PoolNotFoundException:
      return "PoolNotFound: No pool found with the specified ID", 404


@app.route('/pool/create', methods=['POST'])
@with_session
def create_pool(session):
    """
    Creates a new pool, based on the specifications supplied in the request body
    """
    data = request.get_json()
    created_pool = pool.create(session, data)
    return created_pool, 201

@app.route('/pool/settings/update', methods=['POST'])
@with_session
def update_pool_settings(session):
    """
    Update a pool attribute
    """
    data = request.get_json()
    updated_pool = pool.update_settings(session, data)
    return updated_pool, 200

@app.route('/pool/join', methods=['POST'])
@with_session
def join_pool(session):
    """
    Adds the specified user as a member of the given pool
    """
    data = request.get_json()
    try:
      pool.join(session, data)
      return "", 201
    
    except InvalidPoolPasswordException:
      return "Invalid Credentials: The supplied pool password is incorrect", 401
        

@app.route('/pool/transaction/create', methods=['POST'])
@with_session
def create_transaction(session):
    """
    Creates a new transaction record
    """
    data = request.get_json()
    try:
        amount, type = pool.create_transaction(session, data)
        return {
            'amount': amount,
            'type': type
        }, 201
    except InvalidTransactionException:
        return "Invalid Transaction Error: The provided transaction was invalid", 400


@app.route('/login', methods=['POST'])
@with_session
def login(session):
    data = request.get_json()
    try:
      profile_data = user.login(session, data)
      return {
      "jwt": auth.generate_jwt(profile_data)
    }

    except EmailNotFoundException:
        return "EmailNotFound: No profile with the given email could be found", 404
    except InvalidUserPasswordException:
        return "Invalid Credentials: The supplied username and password are invalid", 401
    
    
@app.route('/logout', methods=['GET'])
@with_session
def logout(session):
    return "", 200
    

@app.route('/signup', methods=['POST'])
@with_session
def signup(session):
    data = request.get_json()
    try:
      user.create(session, data)
      return "", 201

    except EmailAlreadyExistsException:
      return "EmailAlreadyExists: A profile with the given email already exists within the database", 401
    
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
