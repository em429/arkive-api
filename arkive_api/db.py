import sqlite3

from .logging import logger
from .utils import strip_url_scheme

      
QUERIES = {
    "store": (
        "INSERT OR IGNORE INTO webpage "
        "([url], [wayback_url]) VALUES "
        "( :url, :wayback_url)"
    ),
    "update": (
        "UPDATE webpage SET wayback_url = :wayback_url "
        "WHERE url = :url"
    ),
    "select": (
        "SELECT * FROM webpage WHERE url = :url_stripped"
    ),
}


class Db:
    name = "arkive.db"
    schema_path = "db_schema.sql"

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def __init__(self, db_name, schema_path):
        self.name: str = db_name
        self.conn = sqlite3.connect(db_name)
        self.schema = """
            CREATE TABLE IF NOT EXISTS webpage (
                [timestamp] DATE DEFAULT (datetime('now', 'utc')),
                [url] TEXT UNIQUE NOT NULL,
                [wayback_url] TEXT DEFAULT NULL
                -- [original_title] TEXT NOT NULL,
                -- [freeze_dried?] BOOLEAN NOT NULL CHECK (solo in (0, 1)),
                -- [freezedry_path] TEXT DEFAULT NULL,
            );
        """
        db_curs = self.conn.cursor()
        db_curs.execute(self.schema)
        self.conn.commit()


async def is_url_in_db(url: str, db_conn):
    url_stripped = strip_url_scheme(url)

    db_curs = db_conn.cursor()
    matched = db_curs.execute(QUERIES['select'], (url_stripped,)).fetchone()

    if matched:
        logger.info("(is_url_in_db) => " + url_stripped + " already in database")
        return matched

    logger.info("(is_url_in_db) => " + url_stripped + " not yet in database")
    return False


async def save_url_to_db(url: str, db_conn):
    url_stripped = strip_url_scheme(url)
    logger.info("(save_url_to_db) => 'insert or ignore' " + url_stripped + " to database")

    db_curs = db_conn.cursor()
    db_curs.execute(QUERIES['store'], (url_stripped, None))
    db_conn.commit()

    return url_stripped


async def update_url_in_db(url_stripped: str, wayback_url: str,  db_conn):
    db_curs = db_conn.cursor()
    db_curs.execute(
        QUERIES['update'], {"wayback_url": wayback_url,
                            "url": url_stripped})
    db_conn.commit()
