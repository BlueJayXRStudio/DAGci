import sys, os, _bootstrap
from datetime import datetime
import sqlite3, json
import uuid
from uuid import UUID

# WIP: IGNORE
class RunLogger:
    def __init__(self, db_path, blob_dir):
        self.db_path = db_path
        self.blob_dir = blob_dir
        self.uuid = None
        self.workflow = None
        self.status = None
        self.created_at = None
        self.started_at = None
        self.completed_at = None
        self.graph_data = None
    
    def init_db_blob(self):
        ''' Idempotent DB and blob storage initialization. '''
        if not self.db_path or not self.blob_dir:
            return False
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.blob_dir, exist_ok=True)
        
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
                started_at TEXT,
                completed_at TEXT
            )
        '''
        )
        conn.commit()
        conn.close()
        return True

    def gen_uuid(self) -> UUID:
        return uuid.uuid4()
    
    def save(self):
        self.uuid = str(self.gen_uuid())
        blob_path = os.path.join(self.blob_dir, f"{self.uuid}.json")

        # write the blob
        with open(blob_path, "w") as f:
            json.dump(self.graph_data, f, indent=2)

        # write metadata
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
                INSERT INTO runs (
                    uuid, workflow, status, 
                    created_at, started_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, 
            (
                self.uuid, self.workflow, self.status,
                self.created_at, self.started_at, self.completed_at
            )
        )
        conn.commit()
        conn.close()
        
    def load(self, uuid):
        self.uuid = uuid
        blob_path = os.path.join(self.blob_dir, f"{uuid}.json")
        with open(blob_path, "r") as f:
            self.graph_data = json.load(f)

