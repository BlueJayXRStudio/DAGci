import sys, os, _bootstrap
from datetime import datetime
import sqlite3
import uuid
from uuid import UUID

# WIP: IGNORE
class RunLogger:
    def __init__(self, db_path):
        self.db_path = db_path
        self.uuid = None
        self.workflow = None
        self.status = None
        self.created_at = None
        self.completed_at = None
        self.graph_data = None
    
    def init_db(self):
        ''' Idempotent DB initialization. '''
        if not self.db_path:
            return False
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                f.write("") 

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
        '''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                workflow TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT
            )
        '''
        )
        conn.commit()
        conn.close()
        return True

    def gen_uuid(self) -> UUID:
        return uuid.uuid4()

    def serialize(self):
        pass

    def deserialize(self):
        pass

