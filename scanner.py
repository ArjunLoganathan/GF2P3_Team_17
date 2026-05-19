"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""


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
        """Open specified file and initialise reserved words and IDs."""
        self.path = path
        self.names = names
        self.file = self.open_file(path)

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""

    def open_file(self):
        """Open and return the file specified by path."""
        try:
            file = open(self.path,"r")
            return file
        except (OSError, IOError) as e:
            raise FileNotFoundError("The provided path was not found!")
        
    def get_next_character(self):
        """Read and return the next character in input_file."""
        try:
            return self.file.read(1)
        except Exception as e:
            raise Exception(f"Exception: {e}")
