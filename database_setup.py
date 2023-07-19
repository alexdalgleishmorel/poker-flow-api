import database
from models import Base

Base.metadata.create_all(database.DatabaseConnector.get_engine())
