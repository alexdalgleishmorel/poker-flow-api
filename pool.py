import bcrypt
from sqlalchemy import select, desc

from models import Pool, PoolMember, PoolSettings, Transaction, TransactionTypes, TransactionStatus
from user import get_user_first_last

class PoolNotFoundException(Exception):
    pass

class PoolSettingsNotFoundException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass

class InvalidTransactionException(Exception):
    pass

def get_by_user_id(session, id, itemOffset, per_page):
    """
    Queries for pools associated with the given user ID
    """
    pools = []

    query = (
        select(PoolMember)
            .join(Pool, Pool.id == PoolMember.pool_id)
            .filter(PoolMember.profile_id == id)
            .order_by(desc(Pool.last_modified))
            .limit(per_page)
            .offset(itemOffset)
        )
    rows = session.execute(query)
    if not rows:
        raise PoolNotFoundException
    
    for row in rows:
        pools.append(get_pool_data(row[0].pool_id, session))

    return pools

def get_by_device_id(session, id, itemOffset, per_page):
    """
    Queries for pools associated with the given device ID
    """
    pools = []

    query = select(Pool).filter_by(device_id=id).order_by(desc(Pool.last_modified))
    paginatedQuery = query.limit(per_page).offset(itemOffset)
    rows = session.execute(paginatedQuery)
    if not rows:
        raise PoolNotFoundException
    
    for row in rows:
        pools.append(get_pool_data(row[0].id, session))

    return pools

def get_by_id(session, id):
    """
    Queries for a pool with the given pool ID
    """
    query = select(Pool).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise PoolNotFoundException
    
    return get_pool_data(rows[0].id, session)

def create(session, specs):
    """
    Creates a new pool, based on the given specifications
    """
    # Create the pool settings
    poolSettings = PoolSettings(
        min_buy_in = specs['settings']['min_buy_in'],
        max_buy_in = specs['settings']['max_buy_in'],
        denominations = ','.join(str(x) for x in specs['settings']['denominations']),
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

    return get_by_id(session, pool.id)

def join(session, data):
    """
    Adds a new member to a pool
    """
    pool = get_by_id(session, data['pool_id'])
    
    query = select(PoolSettings).filter_by(id=pool['settings']['id'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise PoolSettingsNotFoundException
    
    settings = rows[0]
    password = data['password'] if settings.has_password else ''

    # Verify the provided password
    if not bcrypt.checkpw(password.encode('utf-8'), settings.hash.encode('utf-8')):
        raise InvalidPasswordException

    # Add the user as a member
    add_pool_member(data['profile_id'], data['pool_id'], session)

    session.commit()

def create_transaction(session, data):
    """
    Creates a new transaction record
    """
    if data['type'] == TransactionTypes.BUY_IN:
        return create_buy_in(session, data)
    elif data['type'] == TransactionTypes.CASH_OUT:
        return create_cash_out(session, data)
    else:
        raise InvalidTransactionException

def create_buy_in(session, data):
    # Gets the associated pool
    query = select(Pool).filter_by(id=data['pool_id'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise PoolNotFoundException
    pool = rows[0]

    # Creates the transaction
    transaction = Transaction(
        transaction_id = None,
        pool_id = pool.id,
        profile_id = data['profile_id'],
        type = TransactionTypes.BUY_IN,
        amount = data['amount'],
        status = TransactionStatus.PENDING
    )
    session.add(transaction)
    session.flush()

    pool.total_pot += transaction.amount
    pool.available_pot += transaction.amount

    session.commit()
    return transaction.amount, transaction.type

def create_cash_out(session, data):
    # Gets the associated pool
    query = select(Pool).filter_by(id=data['pool_id'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise PoolNotFoundException
    pool = rows[0]

    # Adjusts transaction amount based on the available pot
    transaction_amount = pool.available_pot if data['amount'] > pool.available_pot else data['amount']

    # Creates the transaction
    transaction = Transaction(
        transaction_id = None,
        pool_id = pool.id,
        profile_id = data['profile_id'],
        type = TransactionTypes.CASH_OUT,
        amount = transaction_amount,
        status = TransactionStatus.PENDING
    )
    session.add(transaction)
    session.flush()

    pool.available_pot -= transaction.amount

    session.commit()
    return transaction.amount, transaction.type

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
    pool_admin = get_user_first_last(pool.admin_id, session)
    pool_contributors_dict = {}
    pool_contributors = []
    pool_transactions = []

    query = select(Transaction).filter_by(pool_id=pool_id)
    rows = session.execute(query).all()

    for transaction in rows:
        transaction = transaction[0]
        if not transaction.profile_id in pool_contributors_dict:
            pool_contributors_dict[transaction.profile_id] = {
                "profile": get_user_first_last(transaction.profile_id, session),
                "contribution": transaction.amount if transaction.type == TransactionTypes.BUY_IN else 0
            }
        else:
            pool_contributors_dict[transaction.profile_id]['contribution'] += transaction.amount if transaction.type == TransactionTypes.BUY_IN else 0

        pool_transactions.append({
            "profile": get_user_first_last(transaction.profile_id, session),
            "date": transaction.date,
            "type": transaction.type,
            "amount": transaction.amount
        })

    for contributor in pool_contributors_dict:
        pool_contributors.append(pool_contributors_dict[contributor])
    
    pool_settings = get_settings_data(pool.settings_id, session)

    query = select(PoolMember).filter_by(pool_id=pool_id)
    rows = session.execute(query).all()

    members = []
    for member in rows:
        member = member[0]
        members.append(member.profile_id)

    return {
        'name': pool_name,
        'date_created': date_pool_created,
        'id': pool_id,
        'device_id': device_id,
        'available_pot': available_pot,
        'member_ids': members,
        'contributors': pool_contributors,
        'transactions': pool_transactions,
        'admin': pool_admin,
        'settings': pool_settings,
    }

def get_settings_data(id, session):
    query = select(PoolSettings).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise PoolSettingsNotFoundException
    
    settings = rows[0]

    return {
        "id": settings.id,
        "min_buy_in": settings.min_buy_in,
        "max_buy_in": settings.max_buy_in,
        "denominations": [float(x) for x in settings.denominations.split(',')],
        "has_password": settings.has_password,
        'buy_in_enabled': settings.buy_in_enabled,
        'buy_in_expiry_time': settings.buy_in_expiry_time,
        'expired': settings.expired
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

def update_settings(session, data):
    for updateRequest in data['update_requests']:
        # Gets the associated pool
        query = select(Pool).filter_by(id=data['pool_id'])
        rows = session.execute(query).fetchone()
        if not rows:
            raise PoolNotFoundException
        pool = rows[0]

        query = select(PoolSettings).filter_by(id=pool.settings_id)
        rows = session.execute(query).fetchone()
        if not rows:
            raise PoolSettingsNotFoundException
        settings = rows[0]

        setattr(settings, updateRequest['attribute'], updateRequest['value'])
        
    session.commit()
    return get_pool_data(pool.id, session)
