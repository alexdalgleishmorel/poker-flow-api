import constants

def get_by_user_id(id):
    """
    Queries for pools associated with the given user ID
    """
    return [constants.MOCK_POOL_DATA]

def get_by_device_id(id):
    """
    Queries for pools associated with the given device ID
    """
    return [constants.MOCK_POOL_DATA]

def get_by_id(id):
    """
    Queries for a pool with the given pool ID
    """
    return constants.MOCK_POOL_DATA

def create(specs):
    """
    Creates a new pool, based on the given specifications
    """
    return constants.MOCK_POOL_DATA

def create_transaction(data):
    """
    Creates a new transaction record
    """
    return {
        "response": "stub"
    }
