#!python3

import logging.config

import sqlite3
from sqlite3 import OperationalError

import requests
from requests.exceptions import ConnectionError
from requests.exceptions import MissingSchema


import uvicorn
from fastapi import FastAPI

from urllib.parse import urlparse


from waybackpy import WaybackMachineSaveAPI
from waybackpy.exceptions import TooManyRequestsError

MY_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default_formatter': {
            'format': '[%(levelname)s:%(asctime)s] %(message)s'
        },
    },
    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
        },
    },
    'loggers': {
        'mylogger': {
            'handlers': ['stream_handler'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
logging.config.dictConfig(MY_LOGGING_CONFIG)
logger = logging.getLogger('mylogger')

USER_AGENT = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
IGNORED_URLS = ['favicon.ico']

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

DB_NAME: str = 'arkive.db'
DB_CONN = sqlite3.connect(DB_NAME)


def create_tables(schema_path: str):
    with open(schema_path) as schema:
        db_curs = DB_CONN.cursor()
        db_curs.executescript(schema.read())
        DB_CONN.commit()


try:
    create_tables('db_schema.sql')
except OperationalError as e:
    logger.info("(create_tables) => " + str(e) + "\n")


def strip_url_scheme(url):
    """Strip scheme (e.g. https://, ftp://) from an URL"""
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


async def is_url_in_db(url: str):
    url_stripped = strip_url_scheme(url)

    db_curs = DB_CONN.cursor()
    matched = db_curs.execute(QUERIES['select'], (url_stripped,)).fetchone()

    if matched:
        logger.info("(is_url_in_db) => " + url_stripped + " already in database")
        return matched

    logger.info("(is_url_in_db) => " + url_stripped + " not yet in database")
    return False


async def save_url_to_db(url: str):
    url_stripped = strip_url_scheme(url)
    logger.info("(save_url_to_db) => saving " + url_stripped + " to database")

    db_curs = DB_CONN.cursor()
    db_curs.execute(QUERIES['store'], (url_stripped, None))
    DB_CONN.commit()

    return url_stripped


async def submit_to_internet_archive(url_stripped: str):
    logger.info("(submit_to_internet_archive) => submitting " + url_stripped  + " to Archive.org ..")
    save_api = WaybackMachineSaveAPI(url_stripped, USER_AGENT)
    wayback_url: str = save_api.save()

    logger.info("(submit_to_internet_archive) => saving ia url to db.. ")
    db_curs = DB_CONN.cursor()
    db_curs.execute(
        QUERIES['update'], {"wayback_url": wayback_url,
                            "url": url_stripped})
    DB_CONN.commit()

    return wayback_url


async def is_path_url(url: str):
    """A Somewhat contrived way to check if path is an asset or an url."""
    if url in IGNORED_URLS:
        logger.info('(is_path_url) => ' + url + ' found in ignored list, skipping submit')
        return False

    try:
        logger.info("(is_path_url) ? " + url)
        requests.get(url)
        logger.info("(is_path_url) => True")
        return True
    except ConnectionError:
        logger.info("(is_path_url) => False")
        return False
    except MissingSchema:
        try:
            requests.get('http://' + url)
            logger.info("(is_path_url) => True")
            return True
        except ConnectionError:
            logger.info("(is_path_url) => False")
            return False


app = FastAPI()


@app.get("/")
async def read_root():
    return {"status": "success"}


@app.get("/{url:path}")
async def read_url(url: str):

    # Abort if 'url' turns out to be a path
    if not await is_path_url(url):
        return

    check_db = await is_url_in_db(url)

    # Abort if URL already in database with the requested archive provider's
    # column filled out.
    if check_db and check_db[2]:
        return

    # TODO: return if url is in database and has requested archive url
    # if is_url_in_db(url) and :
    #     return

    try:
        url_stripped = await save_url_to_db(url)
        wayback_url = await submit_to_internet_archive(url_stripped)
        # TODO: deal w/ updating database with wayback_url
        return {
            "status": "success",
            "wayback_url": wayback_url
        }
    except TooManyRequestsError as e:
        logger.info("(read_url) => TooManyRequestsError: " + str(e))
        return {
            "status": "error"
        }


def dev():
    """Launched with `poetry run dev` at root level"""
    uvicorn.run("arkive_api.api:app", port=3000, reload=True)


def prod():
    """Launched with `poetry run prod` at root level"""
    uvicorn.run("arkive_api.api:app", port=3042, reload=False)
