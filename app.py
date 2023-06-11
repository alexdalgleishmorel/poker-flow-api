import flask
from flask import request, jsonify
from flask_cors import CORS

import auth
import pool
import user
from user import EmailAlreadyExistsException

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
    return pool.get_by_user_id(id)

@app.route('/pool/device/<string:id>', methods=['GET'])
def get_pools_by_device_id(id):
    """
    Queries for pools associated with the given device ID
    """
    return pool.get_by_device_id(id)

@app.route('/pool/<string:id>', methods=['GET'])
def get_pool_by_id(id):
    """
    Queries for a pool with the given pool ID
    """
    return pool.get_by_id(id)

@app.route('/pool/create', methods=['POST'])
def create_pool():
    """
    Creates a new pool, based on the specifications supplied in the request body
    """
    return pool.create(request.get_json())

@app.route('/pool/transaction', methods=['POST'])
def create_transaction():
    """
    Creates a new transaction record
    """
    return pool.create_transaction(request.get_json())

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    return {
        "jwt": auth.generate_jwt(data)
    }

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:
      user.create(data)
      return "", 201

    except EmailAlreadyExistsException:
      return "EmailAlreadyExistsException: A profile with the given email already exists within the database", 400
    
if __name__ == '__main__':
    app.run(port=8000)
