import os
from enum import Enum
from .firestore import FirebaseService
from .memory import MemoryService


class DBEnum(str, Enum):

    FIRESTORE = 'FIRESTORE'
    SQL = 'SQL'
    MEMORY = 'MEMORY'


class DatabaseFactory(object):

    @staticmethod
    def get_database(db_type: DBEnum):
        
        if db_type == DBEnum.FIRESTORE:
            instance = FirebaseService()
        elif db_type == DBEnum.MEMORY:
            instance = MemoryService()
        else:
            raise ValueError(f"Database type '{db_type}' not supported. Valid values are [FIRESTORE, MEMORY]")
        
        instance.connect()

        return instance
