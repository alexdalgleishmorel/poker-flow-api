from sqlalchemy import create_engine
import flask
 
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
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')

def get_engine():
    return create_engine(url=f"mssql+pyodbc://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?driver={DRIVER}&{TRUST}")

@app.route('/')
def home():
    try:
        engine = get_engine()
        connection = engine.connect()
        connection.close()
        return 'db connection success'
    except:
        return 'connection failed'
    
if __name__ == '__main__':
    app.run(port=8000)
