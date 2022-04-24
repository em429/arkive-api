#!python3

import logging.config

import sqlite3
from sqlite3 import OperationalError

import requests
from requests.exceptions import ConnectionError


import uvicorn
from fastapi import FastAPI

from urllib.parse import urlparse
from waybackpy import WaybackMachineSaveAPI


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
IGNORED_URLS = [ 'favicon.ico' ]

QUERIES = {
    "store": (
        "INSERT OR IGNORE INTO webpage "
        "([url], [wayback_url]) VALUES "
        "( :url, :wayback_url)"
    )
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


async def archive_webpage(url: str):
    url_stripped = strip_url_scheme(url)

    logger.info("(archive_webpage) => submitting " + url_stripped + " to Archive.org ..")
    save_api = WaybackMachineSaveAPI(url_stripped, USER_AGENT)
    wayback_url: str = save_api.save()

    db_curs = DB_CONN.cursor()
    db_curs.execute(QUERIES['store'], (url, wayback_url))
    DB_CONN.commit()
    logger.info("(archive_webpage) => stored " + url_stripped)
    return wayback_url


app = FastAPI()


@app.get("/")
async def read_root():
    return {"status": "success"}


async def is_path_url(url: str):
    # if url in IGNORED_URLS:
    #     logger.info('(is_path_url) => ' + url + ' found in ignored list, skipping submit')
    #     return False

    try:
        logger.info("(is_path_url) ? " + url)
        requests.get('http://' + url)
        logger.info("(is_path_url) => True")
        return True
    except ConnectionError as e:
        logger.info("(is_path_url) => False with Exception  => " + str(e))
        return False


@app.get("/{url:path}")
async def read_url(url: str):

    if not await is_path_url(url):
        return

    try:
        wayback_url = await archive_webpage(url)
        return {
            "status": "success",
            "wayback_url": wayback_url
        }
    except Exception as e:
        logger.info("(read_url) => Exception: " + str(e))
        return {
            "status": "error"
        }


def dev():
    """Launched with `poetry run dev` at root level"""
    uvicorn.run("arkive_api.api:app", host="0.0.0.0", port=3000, reload=True)


def prod():
    """Launched with `poetry run prod` at root level"""
    uvicorn.run("arkive_api.api:app", host="0.0.0.0", port=3042, reload=False)
