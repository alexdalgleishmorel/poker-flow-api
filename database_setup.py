import database
from models import Base

Base.metadata.create_all(database.get_engine())
