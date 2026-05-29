import pytest
from scanner import Scanner
from names import Names


@pytest.fixture
def create_null_path_scanner():
    '''Create an empty scanner'''
    names = Names()
    scanner = Scanner(path = "scanner_testfile.txt",names = names)
    return scanner

@pytest.fixture
def create_empty_scanner():
    names = Names()

def test_scanners(create_null_path_scanner):
    assert create_null_path_scanner == FileNotFoundError
