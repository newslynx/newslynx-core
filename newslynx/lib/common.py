
from bs4 import BeautifulSoup


def make_soup(html):
    """
    Helper for bs4
    """
    return BeautifulSoup(html, 'html.parser')
