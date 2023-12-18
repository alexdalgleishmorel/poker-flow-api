import boto3
from botocore.exceptions import ClientError
import json
import os

DATABASE = 'pokerflowDB'
DRIVER = 'ODBC+Driver+18+for+SQL+Server'
ENV = os.getenv('env')
API_HOST = '127.0.01'
API_PORT = 8000
CLIENT_HOST = 'localhost'
CLIENT_PORT = 8100
TRUST = 'TrustServerCertificate=yes'

if not ENV:
  raise Exception('Missing environment variable: env')

if ENV == 'prod':
  secret_name = "pokerflow-database-1"
  region_name = "us-east-2"

  # Create a Secrets Manager client
  session = boto3.session.Session()
  client = session.client(
      service_name='secretsmanager',
      region_name=region_name
  )

  try:
      get_secret_value_response = client.get_secret_value(
          SecretId=secret_name
      )
  except ClientError as e:
      raise e

  # Decrypts secret using the associated KMS key.
  secret = json.loads(get_secret_value_response['SecretString'])

  USER = secret['username']
  PASSWORD = secret['password']
  HOST = secret['host']
  PORT = secret['port']

elif ENV == 'local':
  USER = os.getenv('db_username')
  PASSWORD = os.getenv('db_password')
  HOST = os.getenv('db_host')
  PORT = os.getenv('db_port')

else:
   raise Exception(f'Unrecognized env: {ENV}')

if not USER: raise Exception('Missing required environment variable: db_username')
if not PASSWORD: raise Exception('Missing required environment variable: db_password')
if not HOST: raise Exception('Missing required environment variable: db_host')
if not PORT: raise Exception('Missing required environment variable: db_port')
