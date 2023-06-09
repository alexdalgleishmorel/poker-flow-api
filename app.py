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

MOCK_POOL_DATA = {
  'name': 'mock_pool_name',
  'date_created': '01/01/2023 15:21 MDT',
  'id': 'mock_id',
  'device_id': 'mock_device_id',
  'total': 123.45,
  'contributors': [
    {
      'profile': {
        'email': 'alex@local.com',
        'firstName': 'Alex',
        'lastName': 'Dalgleish-Morel'
      },
      'contribution': 83.45
    },
    {
      'profile': {
        'email': 'landan@local.com',
        'firstName': 'Landan',
        'lastName': 'Butt'
      },
      'contribution': 20.55
    },
    {
      'profile': {
        'email': 'kian@local.com',
        'firstName': 'Kian',
        'lastName': 'Reilly'
      },
      'contribution': 20.45
    }
  ],
  'transactions': [
    {
      'id': 'mock_transaction_id',
      'profile': {
        'email': 'alex@local.com',
        'firstName': 'Alex',
        'lastName': 'Dalgleish-Morel'
      },
      'date': '01/01/2023 15:21 MDT',
      'type': 'BUY-IN',
      'amount': 50.51
    },
    {
      'id': 'mock_transaction_id',
      'profile': {
        'email': 'alex@local.com',
        'firstName': 'Alex',
        'lastName': 'Dalgleish-Morel'
      },
      'date': '01/01/2023 16:21 MDT',
      'type': 'CASH-OUT',
      'amount': 40.44
    }
  ],
  'admin': {
    'email': 'alex@local.com',
    'firstName': 'Alex',
    'lastName': 'Dalgleish-Morel'
  },
  'settings': {
    'hasPassword': False,
    'minBuyIn': 5,
    'maxBuyIn': 100,
    'denominations': []
  }
}

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
def get_pools_by_user_id(id):
    """
    Queries for pools associated with the given user ID
    """
    return [MOCK_POOL_DATA]

@app.route('/pool/device/<string:id>', methods=['GET'])
def get_pools_by_device_id(id):
    """
    Queries for pools associated with the given device ID
    """
    return [MOCK_POOL_DATA]

@app.route('/pool/<string:id>', methods=['GET'])
def get_pool_by_id(id):
    """
    Queries for a pool with the given device ID
    """
    return MOCK_POOL_DATA

@app.route('/pool/create', methods=['POST'])
def create_pool():
    """
    Creates a new pool, based on the specifications supplied in the request body
    """
    return MOCK_POOL_DATA

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
    return {
        "jwt": encoded_jwt
    }
    
if __name__ == '__main__':
    app.run(port=8000)
