"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
from primativetypes import TokenType

class Symbol:

    """Encapsulate a symbol and store its properties.

    Parameters
    ----------
    No parameters.

    Public methods
    --------------
    No public methods.
    """

    def __init__(self):
        """Initialise symbol properties."""
        self.type = None
        self.id = None


class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into symbols
    that the parser can use. It also skips over comments and irrelevant
    formatting characters, such as spaces and line breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters into a symbol
                      and returns the symbol.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs.
        Need to write more tests and error correction codes"""
        self.path = path
        self.names = names
        self.current_symbol = None
        self.reservered_keywords = "IMPORT FROM DEVICES CONNECT MONITOR END SWITCH CLOCK AND OR NAND NOR XOR NOT DTYPE".split(" ")
        self.reservered_keyword_ids = self.names.lookup(self.reservered_keywords)
        self.file = self.open_file(path)

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        next_symbols = self.get_next_symbol()
        symbol_id,next_char_id = self.names.lookup(next_symbols)
        self.current_symbol = Symbol()
        self.current_symbol.id = symbol_id
        if symbol_id in self.reservered_keyword_ids:
            self.current_symbol.type = TokenType.KEYWORD
        return self.current_symbol

    def open_file(self):
        """Open and return the file specified by path.
        Need to write more tests and error correction codes"""
        try:
            file = open(self.path,"r")
            return file
        except (OSError, IOError) as e:
            raise FileNotFoundError("The provided path was not found!")
        
    def get_next_character(self):
        """Read and return the next character in input_file.
        Need to write more tests and error correction codes"""
        try:
            return self.file.read(1)
        except Exception as e:
            raise Exception(f"Exception: {e}")
        
    def get_next_non_whitespace_character(self):
        """Seek and return the next non-whitespace character in file."""
        try:
            char = self.file.read(1)
            if char != "" and char.isspace():
                return self.get_next_non_whitespace_character(self.file)
            return char
        except:
            raise Exception(f"Exception - Error in non-whitespace reader!")
        
    def get_next_symbol(self):
        """Seek the next symbol string in input_file.
        Return the symbol string (or None) and the next non-alphanumeric character.
        """
        try:
            char = self.get_next_non_whitespace_character()
            while not char.isalnum():
                if char == ";":
                    return [None,";"]
                char = self.get_next_non_whitespace_character()
        
            temp_str = ""
            while char.isalnum():
                temp_str += char
                char = self.get_next_non_whitespace_character()
            return [temp_str,char]
        except:
            # not sure when this will be called need to write tests for this
            raise Exception("dasdas")
