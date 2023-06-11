import bcrypt
from sqlalchemy import select

import database
from models import Pool, PoolMember, PoolSettings, Transaction, TransactionTypes, TransactionStatus
from user import get_user_first_last

class PoolNotFoundException(Exception):
    pass

class PoolSettingsNotFoundException(Exception):
    pass

def get_by_user_id(id):
    """
    Queries for pools associated with the given user ID
    """
    session = database.get_session()
    pools = []

    try:
        query = select(PoolMember).filter_by(profile_id=id)
        rows = session.execute(query).all()
        if not rows:
            raise PoolNotFoundException
        
        for row in rows:
            pools.append(get_pool_data(row[0].pool_id, session))

    finally:
        session.close()

    return pools

def get_by_device_id(id):
    """
    Queries for pools associated with the given device ID
    """
    session = database.get_session()
    pools = []

    try:
        query = select(Pool).filter_by(device_id=id)
        rows = session.execute(query).all()
        if not rows:
            raise PoolNotFoundException
        
        for row in rows:
            pools.append(get_pool_data(row[0].id, session))

    finally:
        session.close()

    print(pools)

    return pools

def get_by_id(id):
    """
    Queries for a pool with the given pool ID
    """
    session = database.get_session()

    try:
        query = select(Pool).filter_by(id=id)
        rows = session.execute(query).fetchone()
        if not rows:
            raise PoolNotFoundException
        
        return get_pool_data(rows[0].id, session)

    finally:
        session.close()

def create(specs):
    """
    Creates a new pool, based on the given specifications
    """
    session = database.get_session()

    try:
        # Create the pool settings
        poolSettings = PoolSettings(
            min_buy_in = specs['settings']['min_buy_in'],
            max_buy_in = specs['settings']['max_buy_in'],
            denominations = specs['settings']['denominations'],
            has_password = specs['settings']['has_password'],
            hash = bcrypt.hashpw(specs['settings']['password'].encode('utf-8'), bcrypt.gensalt(rounds=12))
        )
        session.add(poolSettings)
        session.flush()

        # Create the pool
        pool = Pool(
            device_id = specs['device_id'],
            pool_name = specs['pool_name'],
            settings_id = poolSettings.id,
            admin_id = specs['admin_id'],
        )
        session.add(pool)
        session.flush()

        # Add the admin as a member
        poolmember = PoolMember(
            pool_id = pool.id,
            profile_id = specs['admin_id']
        )

        session.add(poolmember)

        session.commit()

        return pool.id

    finally:
        session.close()

def create_transaction(data):
    """
    Creates a new transaction record
    """
    session = database.get_session()

    try:
        # Creates the transaction
        transaction = Transaction(
            transaction_id = None,
            pool_id = data['pool_id'],
            profile_id = data['profile_id'],
            type = data['type'],
            amount = data['amount'],
            status = TransactionStatus.PENDING
        )
        session.add(transaction)
        session.flush()

        query = select(Pool).filter_by(id=data['pool_id'])
        rows = session.execute(query).fetchone()
        if not rows:
            raise PoolNotFoundException
        
        if transaction.type == TransactionTypes.BUY_IN:
            rows[0].available_pot += transaction.amount
        else:
            rows[0].available_pot -= transaction.amount

        session.commit()

        return transaction.id

    finally:
        session.close()

def get_pool_data(id, session):
    """
    Gets all data pertaining to a specific pool
    """
    query = select(Pool).filter_by(id=id)
    rows = session.execute(query).all()
    if not rows:
        raise PoolNotFoundException
    
    pool = rows[0][0]
    pool_name = pool.pool_name
    date_pool_created = pool.date_created
    pool_id = pool.id
    available_pot = pool.available_pot
    device_id = pool.device_id
    pool_admin = pool.admin_id
    pool_contributors = {}
    pool_transactions = {}

    query = select(Transaction).filter_by(pool_id=pool_id)
    rows = session.execute(query).all()

    for transaction in rows:
        transaction = transaction[0]
        if not transaction.profile_id in pool_contributors:
            pool_contributors[transaction.profile_id] = {
                "profile": get_user_first_last(transaction.profile_id, session),
                "amount": transaction.amount if transaction.type == TransactionTypes.BUY_IN else 0
            }
        else:
            pool_contributors[transaction.profile_id]['amount'] += transaction.amount if transaction.type == TransactionTypes.BUY_IN else 0

        pool_transactions[transaction.id] = {
            "profile": get_user_first_last(transaction.profile_id, session),
            "date": transaction.date,
            "type": transaction.type,
            "amount": transaction.amount
        }
    
    pool_settings = get_settings_data(pool.settings_id, session)

    return {
        'name': pool_name,
        'date_created': date_pool_created,
        'id': pool_id,
        'device_id': device_id,
        'available_pot': available_pot,
        'contributors': pool_contributors,
        'transactions': pool_transactions,
        'admin': pool_admin,
        'settings': pool_settings
    }

def get_settings_data(id, session):
    query = select(PoolSettings).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise PoolSettingsNotFoundException
    
    settings = rows[0]

    return {
        "min_buy_in": settings.min_buy_in,
        "max_buy_in": settings.max_buy_in,
        "denominations": settings.denominations,
        "has_password": settings.has_password
    }

def add_pool_member(id, pool_id, session):
    query = select(PoolMember).filter_by(profile_id=id, pool_id=pool_id)
    rows = session.execute(query).all()
    if rows:
        return
    poolmember = PoolMember(
        pool_id = pool_id,
        profile_id = id
    )
    session.add(poolmember)
