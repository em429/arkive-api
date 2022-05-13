import sqlite3

from .logging import logger
from .utils import strip_url_scheme

QUERIES = {
    "store": (
        "INSERT OR IGNORE INTO webpage "
        "([url], [internet_archive_url]) VALUES "
        "( :url, :internet_archive_url)"
    ),
    "update": (
        "UPDATE webpage SET internet_archive_url = :internet_archive_url "
        "WHERE url = :url"
    ),
    "select": (
        "SELECT * FROM webpage WHERE url = :url_stripped"
    ),
}


class Db:
    name = "arkive.db"
    schema_path = "db_schema.sql"
    schema = """
        CREATE TABLE IF NOT EXISTS webpage (
            [timestamp] DATE DEFAULT (datetime('now', 'utc')),
            [url] TEXT UNIQUE NOT NULL,
            [internet_archive_url] TEXT DEFAULT NULL,
            [archive_today_url] TEXT DEFAULT NULL,
            [original_title] TEXT DEFAULT NULL,
            [to_freeze_dry] BOOLEAN DEFAULT 1 CHECK (to_freeze_dry in (0, 1)),
            [freezedry_path] TEXT DEFAULT NULL,
            [read] BOOLEAN DEFAULT 0 CHECK (read in (0, 1)),
            [hidden] BOOLEAN DEFAULT 0 CHECK (read in (0, 1))
            -- [full_extracted_text] TEXT DEFAULT NULL,
        );
    """

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def __init__(self, db_name, schema_path):
        self.name: str = db_name
        self.conn = sqlite3.connect(db_name)
        # Create table if doesn't exist:
        curs = self.conn.cursor()
        curs.execute(self.schema)
        self.conn.commit()


async def is_url_in_db(url: str, conn):
    url_stripped = strip_url_scheme(url)

    curs = conn.cursor()
    matched = curs.execute(QUERIES['select'], (url_stripped,)).fetchone()

    if matched:
        logger.info("(is_url_in_db) => " +
                    url_stripped + " already in database")
        return matched

    logger.info("(is_url_in_db) => " + url_stripped + " not yet in database")
    return False


async def save_url(url: str, conn):
    url_stripped = strip_url_scheme(url)
    logger.info("(save_url) => 'insert or ignore' " +
                url_stripped + " to database")

    curs = conn.cursor()
    curs.execute(QUERIES['store'], (url_stripped, None))
    conn.commit()

    return url_stripped


async def hide_url(url: str, conn):
    url_stripped = strip_url_scheme(url)
    logger.info("(hide_url) => " +
                url_stripped + "")
    curs = conn.cursor()
    curs.execute("UPDATE webpage SET hidden = 1 WHERE url = ?", (url_stripped,))
    conn.commit()

    return url_stripped

async def unhide_url(url: str, conn):
    url_stripped = strip_url_scheme(url)
    logger.info("(uhide_url) => " +
                url_stripped + "")
    curs = conn.cursor()
    curs.execute("UPDATE webpage SET hidden = 0 WHERE url = ?", (url_stripped,))
    conn.commit()

    return url_stripped


# TODO: remove unecessary _in_db, db_
async def update_url(url_stripped: str, internet_archive_url: str,  conn):
    curs = conn.cursor()
    curs.execute(
        QUERIES['update'], {"internet_archive_url": internet_archive_url,
                            "url": url_stripped})
    conn.commit()

