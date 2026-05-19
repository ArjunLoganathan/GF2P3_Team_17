import pytest
from scanner import Scanner
from names import Names


@pytest.fixture
def create_scanner(path):
    '''Create an empty scanner'''
    names = Names()
    scanner = Scanner(path = path,names = names)
    return scanner

