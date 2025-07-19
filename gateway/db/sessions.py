import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


DB_FILE = 'local.db'

ENGINE = create_engine(
    f'sqlite:///{DB_FILE}',
    connect_args={'check_same_thread': False},
)

SessionMaker = sessionmaker(ENGINE)


def init_db(clear=False):
    db_file = Path(DB_FILE).resolve()
    if clear and db_file.is_file():
        os.remove(db_file)
    Base.metadata.create_all(ENGINE)
    return


def get_session():
    return SessionMaker()
