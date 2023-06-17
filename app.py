import flask
from flask import request, jsonify
from flask_cors import CORS

import auth
import pool
from pool import PoolNotFoundException
import user
from user import EmailAlreadyExistsException, EmailNotFoundException, InvalidPasswordException

class PrefixMiddleware(object):

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]

app = flask.Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "http://localhost:4200"}})
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')


@app.route('/pool/user/<string:id>', methods=['GET'])
def get_pools_by_user_id(id):
    """
    Queries for pools associated with the given user ID
    """
    try:
        pools = pool.get_by_user_id(id)
        return jsonify(pools)
    except PoolNotFoundException:
        return "PoolNotFound: No pools found relating to the specified user ID", 404


@app.route('/pool/device/<string:id>', methods=['GET'])
def get_pools_by_device_id(id):
    """
    Queries for pools associated with the given device ID
    """
    try:
        pools = pool.get_by_device_id(id)
        return jsonify(pools)
    except PoolNotFoundException:
        return "PoolNotFound: No pools found relating to the specified device ID", 404


@app.route('/pool/<string:id>', methods=['GET'])
def get_pool_by_id(id):
    """
    Queries for a pool with the given pool ID
    """
    try:
        pool_data = pool.get_by_id(id)
        return jsonify(pool_data)
    except PoolNotFoundException:
        return "PoolNotFound: No pool found with the specified ID", 404


@app.route('/pool/create', methods=['POST'])
def create_pool():
    """
    Creates a new pool, based on the specifications supplied in the request body
    """
    created_pool = pool.create(request.get_json())
    return created_pool, 201


@app.route('/pool/transaction/create', methods=['POST'])
def create_transaction():
    """
    Creates a new transaction record
    """
    pool.create_transaction(request.get_json())
    return "", 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
      profile_data = user.login(data)
      return {
      "jwt": auth.generate_jwt(profile_data)
    }

    except EmailNotFoundException:
        return "EmailNotFound: No profile with the given email could be found", 404
    except InvalidPasswordException:
        return "Invalid Credentials: The supplied username and password are invalid", 401


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:
      user.create(data)
      return "", 201

    except EmailAlreadyExistsException:
      return "EmailAlreadyExists: A profile with the given email already exists within the database", 401
    
if __name__ == '__main__':
    app.run(port=8000)
