from sqlalchemy import create_engine
import flask
from flask import request
from flask_cors import CORS
import jwt
 
# DEFINE THE DATABASE CREDENTIALS
USER = 'sa'
PASSWORD = '(oolFrog45!!'
HOST = '127.0.0.1'
PORT = '1433'
DATABASE = 'pokerflowDB'

# DEFINE SETTINGS
DRIVER = 'ODBC+Driver+18+for+SQL+Server'
TRUST = 'TrustServerCertificate=yes'

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

def get_engine():
    return create_engine(url=f"mssql+pyodbc://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?driver={DRIVER}&{TRUST}")

@app.route('/pool/user/<string:id>', methods=['GET'])
def get_pool_by_user_id(id):
    """
    Queries for pools associated with the given user ID
    """
    return {
        "response": "stub"
    }

@app.route('/pool/device/<string:id>', methods=['GET'])
def get_pool_by_device_id(id):
    """
    Queries for pools associated with the given device ID
    """
    return {
        "response": "stub"
    }

@app.route('/pool/<string:id>', methods=['GET'])
def get_pool_by_id(id):
    """
    Queries for a pool with the given device ID
    """
    return {
        "response": "stub"
    }

@app.route('/pool/create', methods=['POST'])
def create_pool():
    """
    Creates a new pool, based on the specifications supplied in the request body
    """
    return {
        "response": "stub"
    }

@app.route('/pool/transaction', methods=['POST'])
def create_transaction():
    """
    Creates a new transaction record
    """
    return {
        "response": "stub"
    }

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    encoded_jwt = jwt.encode(
        {
            "profile": {
                "id": "stub_user_id",
                "email": f"{data['email']}",
                "firstName": "stub_first_name",
                "lastName": "stub_last_name",
            },
            "jwt": "mock_jwt_token_from_api"
        }, 
        "secret", 
        algorithm="HS256"
    )
    return {
        "jwt": encoded_jwt
    }

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    encoded_jwt = jwt.encode(
        {
            "profile": {
                "id": "stub_user_id",
                "email": f"{data['email']}",
                "firstName": f"{data['firstName']}",
                "lastName": f"{data['lastName']}",
            },
            "jwt": "mock_jwt_token_from_api"
        }, 
        "secret", 
        algorithm="HS256"
    )
    return encoded_jwt
    
if __name__ == '__main__':
    app.run(port=8000)
