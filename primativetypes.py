from enum import Enum, auto

class TokenType(Enum):
    KEYWORD = auto()
    NAME = auto()
    NUMBER = auto()
    STRING = auto()
    COLON = auto()
    SEMICOLON = auto()
    EQUALS = auto()
    DOT = auto()
    EOF = auto()
    INVALID = auto()