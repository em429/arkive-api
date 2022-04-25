from urllib.parse import urlparse

from requests import get
from requests.exceptions import MissingSchema

from .logging import logger

IGNORED_URLS = ['favicon.ico']


def strip_url_scheme(url):
    """Strip scheme (e.g. https://, ftp://) from an URL"""
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


async def is_path_url(url: str):
    """A Somewhat contrived way to check if path is an asset or an url."""
    if url in IGNORED_URLS:
        logger.info('(is_path_url) => ' + url + ' found in ignored list, skipping submit')
        return False

    try:
        logger.info("(is_path_url) ? " + url)
        get(url)
        logger.info("(is_path_url) => True")
        return True
    except ConnectionError:
        logger.info("(is_path_url) => False")
        return False
    except MissingSchema:
        try:
            get('http://' + url)
            logger.info("(is_path_url) => True")
            return True
        except ConnectionError:
            logger.info("(is_path_url) => False")
            return False
