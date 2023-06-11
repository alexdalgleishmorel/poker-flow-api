USER = 'sa'
PASSWORD = '(oolFrog45!!'
HOST = '127.0.0.1'
PORT = '1433'
DATABASE = 'pokerflowDB'

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
