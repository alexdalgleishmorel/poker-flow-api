import bcrypt
from sqlalchemy import select, desc

from models import Game, GameMember, GameSettings, Transaction, TransactionTypes
from user import get_user_first_last

class GameNotFoundException(Exception):
    pass

class GameSettingsNotFoundException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass

class InvalidTransactionException(Exception):
    pass

def get_by_user_id(session, id, itemOffset, per_page, expired):
    """
    Queries for games associated with the given user ID
    """
    games = []

    query = (
        select(GameMember)
            .join(Game, Game.id == GameMember.game_id)
            .join(GameSettings, Game.settings_id == GameSettings.id)
            .filter(GameMember.profile_id == id)
            .filter(GameSettings.expired == expired)
            .order_by(desc(Game.last_modified))
            .limit(per_page)
            .offset(itemOffset)
        )
    rows = session.execute(query)
    if not rows:
        raise GameNotFoundException
    
    for row in rows:
        games.append(get_game_data(row[0].game_id, session))

    return games

def get_by_id(session, id):
    """
    Queries for a game with the given game ID
    """
    query = select(Game).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameNotFoundException
    
    return get_game_data(rows[0].id, session)

def create(session, specs):
    """
    Creates a new game, based on the given specifications
    """
    # Create the game settings
    gameSettings = GameSettings(
        min_buy_in = specs['settings']['minBuyIn'],
        max_buy_in = specs['settings']['maxBuyIn'],
        denominations = ','.join(str(x) for x in specs['settings']['denominations']),
    )
    session.add(gameSettings)
    session.flush()

    # Create the game
    game = Game(
        name = specs['name'],
        settings_id = gameSettings.id,
        admin_id = specs['adminID'],
    )
    session.add(game)
    session.flush()

    # Add the admin as a member
    game_member = GameMember(
        game_id = game.id,
        profile_id = specs['adminID']
    )

    session.add(game_member)

    session.commit()

    return get_by_id(session, game.id)

def join(session, data):
    """
    Adds a new member to a game
    """
    game = get_by_id(session, data['gameID'])
    
    query = select(GameSettings).filter_by(id=game['settings']['id'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameSettingsNotFoundException

    # Add the user as a member
    add_game_member(data['profileID'], data['gameID'], session)

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
    # Gets the associated game
    query = select(Game).filter_by(id=data['gameID'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameNotFoundException
    game = rows[0]

    # Creates the transaction
    transaction = Transaction(
        game_id = game.id,
        profile_id = data['profileID'],
        type = TransactionTypes.BUY_IN,
        amount = data['amount'],
    )
    session.add(transaction)
    session.flush()

    game.total_pot += transaction.amount
    game.available_cashout += transaction.amount

    session.commit()
    return transaction.amount, transaction.type

def create_cash_out(session, data):
    # Gets the associated game
    query = select(Game).filter_by(id=data['gameID'])
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameNotFoundException
    game = rows[0]

    # Adjusts transaction amount based on the available cashout
    transaction_amount = data['amount']

    if data['amount'] >= game.available_cashout:
        transaction_amount = game.available_cashout
        get_game_settings(game.settings_id, session).expired = True

    # Creates the transaction
    transaction = Transaction(
        game_id = game.id,
        profile_id = data['profileID'],
        type = TransactionTypes.CASH_OUT,
        amount = transaction_amount,
    )
    session.add(transaction)
    session.flush()

    game.available_cashout -= transaction.amount

    session.commit()
    return transaction.amount, transaction.type

def get_game_data(id, session):
    """
    Gets all data pertaining to a specific game
    """
    query = select(Game).filter_by(id=id)
    rows = session.execute(query).all()
    if not rows:
        raise GameNotFoundException
    
    game = rows[0][0]
    name = game.name
    date_game_created = game.date_created
    game_id = game.id
    available_cashout = game.available_cashout
    game_admin = get_user_first_last(game.admin_id, session)
    game_contributors_dict = {}
    game_contributors = []
    game_transactions = []

    query = select(Transaction).filter_by(game_id=game_id)
    rows = session.execute(query).all()

    for transaction in rows:
        transaction = transaction[0]
        if not transaction.profile_id in game_contributors_dict:
            game_contributors_dict[transaction.profile_id] = {
                "profile": get_user_first_last(transaction.profile_id, session),
                "contribution": transaction.amount if transaction.type == TransactionTypes.BUY_IN else 0
            }
        else:
            game_contributors_dict[transaction.profile_id]['contribution'] += transaction.amount if transaction.type == TransactionTypes.BUY_IN else 0

        game_transactions.append({
            "profile": get_user_first_last(transaction.profile_id, session),
            "date": transaction.date,
            "type": transaction.type,
            "amount": transaction.amount
        })

    for contributor in game_contributors_dict:
        game_contributors.append(game_contributors_dict[contributor])
    
    game_settings = get_settings_data(game.settings_id, session)

    query = select(GameMember).filter_by(game_id=game_id)
    rows = session.execute(query).all()

    members = []
    for member in rows:
        member = member[0]
        members.append(member.profile_id)

    return {
        'name': name,
        'dateCreated': date_game_created,
        'id': game_id,
        'availableCashout': available_cashout,
        'memberIDs': members,
        'contributors': game_contributors,
        'transactions': game_transactions,
        'admin': game_admin,
        'settings': game_settings,
    }

def get_game_settings(id, session):
    query = select(GameSettings).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameSettingsNotFoundException
    
    return rows[0]

def get_settings_data(id, session):
    query = select(GameSettings).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameSettingsNotFoundException
    
    settings = rows[0]

    return {
        "id": settings.id,
        "minBuyIn": settings.min_buy_in,
        "maxBuyIn": settings.max_buy_in,
        "denominations": [float(x) for x in settings.denominations.split(',')],
        'buyInEnabled': settings.buy_in_enabled,
        'expired': settings.expired
    }

def add_game_member(id, game_id, session):
    query = select(GameMember).filter_by(profile_id=id, game_id=game_id)
    rows = session.execute(query).all()
    if rows:
        return
    game_member = GameMember(
        game_id = game_id,
        profile_id = id
    )
    session.add(game_member)

def update_settings(session, data):
    for updateRequest in data['update_requests']:
        # Gets the associated game
        query = select(Game).filter_by(id=data['gameID'])
        rows = session.execute(query).fetchone()
        if not rows:
            raise GameNotFoundException
        game = rows[0]

        query = select(GameSettings).filter_by(id=game.settings_id)
        rows = session.execute(query).fetchone()
        if not rows:
            raise GameSettingsNotFoundException
        settings = rows[0]

        setattr(settings, updateRequest['attribute'], updateRequest['value'])
        
    session.commit()
    return get_game_data(game.id, session)
