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
    Find games where the given user is a member. 
    Supports pagination and filters based on whether the game is expired or not.

    Parameters:
    session (Session): The database session to use for queries.
    id (int): The user ID to search for in the game members.
    itemOffset (int): The offset from where to start the query results, used for pagination.
    per_page (int): The number of items to return per page.
    expired (bool): A flag to filter games based on whether they are expired.

    Returns:
    list: A list of games associated with the given user ID.

    Raises:
    GameNotFoundException: If no games are found for the given user ID.
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
    Queries for a specific game using based on the provided ID.

    Parameters:
    session (Session): The database session to use for the query.
    id (int): The unique identifier of the game to be retrieved.

    Returns:
    dict: A dictionary containing the game's data, if found.

    Raises:
    GameNotFoundException: If no game is found with the provided ID.
    """
    query = select(Game).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameNotFoundException
    
    return get_game_data(rows[0].id, session)

def create(session, specs):
    """
    Handles the creation of a new game, registering the game and its settings to the database.

    Parameters:
    session (Session): The database session to be used for creating the game.
    specs (dict): A dictionary containing the specifications for the new game.

    Returns:
    dict: The data of the newly created game.
    """
    # Create the game settings
    gameSettings = GameSettings(
        min_buy_in = specs['settings']['minBuyIn'],
        max_buy_in = specs['settings']['maxBuyIn'],
        denominations = ','.join(str(x) for x in specs['settings']['denominations']),
        denomination_colors = ','.join(str(x) for x in specs['settings']['denominationColors']),
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
    Registers a user as a member of a specified game.
    Checks for the existence of the game and its settings before adding the member.

    Parameters:
    session (Session): The database session to use for the operation.
    data (dict): A dictionary containing the game ID and the profile ID of the new member.

    Raises:
    GameNotFoundException: If no game is found with the provided game ID.
    GameSettingsNotFoundException: If the settings for the specified game are not found.
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
    Processes games transactions. 
    Supports buy-in and cash-out transactions and ensures valid transaction processing.

    Parameters:
    session (Session): The database session to use for creating the transaction.
    data (dict): A dictionary containing transaction details including type, amount, game ID, and profile ID.

    Raises:
    InvalidTransactionException: If the transaction type is not recognized.
    """
    if data['type'] == TransactionTypes.BUY_IN:
        return create_buy_in(session, data)
    elif data['type'] == TransactionTypes.CASH_OUT:
        return create_cash_out(session, data)
    else:
        raise InvalidTransactionException

def create_buy_in(session, data):
    """
    Processing a buy-in transaction, where a player adds money to the game's pot. 
    Updates the game's total pot and available cashout amounts accordingly.

    Parameters:
    session (Session): The database session to use for the transaction.
    data (dict): A dictionary containing details of the buy-in transaction, including the game ID, profile ID, amount, and denominations.

    Returns:
    tuple: A tuple containing the transaction amount and type.

    Raises:
    GameNotFoundException: If no game is found for the given game ID.
    """
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
        denominations = ','.join(str(x) for x in data['denominations']),
    )
    session.add(transaction)
    session.flush()

    game.total_pot += transaction.amount
    game.available_cashout += transaction.amount

    session.commit()
    return transaction.amount, transaction.type

def create_cash_out(session, data):
    """
    Handles cash-out transactions where a player withdraws money from the game's total pot.
    It adjusts the transaction amount based on the available cashout and updates the game's available cashout accordingly.

    Parameters:
    session (Session): The database session for processing the transaction.
    data (dict): Details of the cash-out transaction, including game ID, profile ID, and requested amount.

    Returns:
    tuple: A tuple containing the processed transaction amount and type.

    Raises:
    GameNotFoundException: If the specified game is not found.
    """
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
        denominations = ','.join(str(x) for x in data['denominations']),
    )
    session.add(transaction)
    session.flush()

    game.available_cashout -= transaction.amount

    session.commit()
    return transaction.amount, transaction.type

def get_game_data(id, session):
    """
    Creates an object containing all required details of a specific game.

    Parameters:
    id (int): The ID of the game to retrieve.
    session (Session): The database session to use for queries.

    Returns:
    dict: A dictionary containing detailed information about the game.

    Raises:
    GameNotFoundException: If no game is found with the provided ID.
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
            "date": transaction.date.isoformat() + 'Z',
            "type": transaction.type,
            "amount": transaction.amount,
            "denominations": [int(x) for x in transaction.denominations.split(',')],
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
        'dateCreated': date_game_created.isoformat() + 'Z',
        'id': game_id,
        'availableCashout': available_cashout,
        'memberIDs': members,
        'contributors': game_contributors,
        'transactions': game_transactions,
        'admin': game_admin,
        'settings': game_settings,
    }

def get_game_settings(id, session):
    """
    Retrieves the settings associated with a specific game.

    Parameters:
    id (int): The ID of the game whose settings are to be retrieved.
    session (Session): The database session to use for the query.

    Returns:
    GameSettings: The game settings object.

    Raises:
    GameSettingsNotFoundException: If no settings are found for the given game ID.
    """
    query = select(GameSettings).filter_by(id=id)
    rows = session.execute(query).fetchone()
    if not rows:
        raise GameSettingsNotFoundException
    
    return rows[0]

def get_settings_data(id, session):
    """
    Creates an object containing all required details of a specific game's settings.

    Parameters:
    id (int): The ID of the game settings for which settings data is required.
    session (Session): The database session for the query.

    Returns:
    dict: A dictionary containing the settings data of the game.

    Raises:
    GameSettingsNotFoundException: If settings for the specified game settings ID are not found.
    """
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
        "denominationColors": [x for x in settings.denomination_colors.split(',')],
        'buyInEnabled': settings.buy_in_enabled,
        'expired': settings.expired
    }

def add_game_member(id, game_id, session):
    """
    Registers a user as a member of a game, if the user is not already a member.

    Parameters:
    id (int): The profile ID of the user to be added as a member.
    game_id (int): The ID of the game to which the member is to be added.
    session (Session): The database session for the operation.
    """
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
    """
    Modifies the game settings of a game based on provided update requests.
    Handles multiple updates in a single transaction.

    Parameters:
    session (Session): The database session to use for updating settings.
    data (dict): A dictionary containing the game ID and a list of update requests, each specifying the attribute to update and its new value.

    Returns:
    dict: The updated game data after the settings have been modified.

    Raises:
    GameNotFoundException: If no game is found for the provided game ID.
    GameSettingsNotFoundException: If settings for the specified game are not found.
    """
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
