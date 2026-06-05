"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
from primativetypes import TokenType
import re


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
        self.line = None


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

    def __init__(self, path, names, source_text=None):
        """Open specified file and initialise reserved words and IDs.
        Need to write more tests and error correction codes"""
        self.path = path
        self.names = names
        self.source_text = source_text
        # self.current_symbol = None
        self.current_line = 1
        # self.reserved_keywords = "IMPORT FROM DEVICES CONNECT MONITOR END SWITCH CLOCK AND OR NAND NOR XOR NOT DTYPE INPUT_PORTS OUTPUT_PORTS".split(" ")
        # self.reserved_keyword_ids = self.names.lookup(self.reserved_keywords)
        self.reserved_keywords = self.names.reserved_keywords
        # self.reserved_keyword_ids = self.names.reserved_keyword_ids
        self.reserved_keyword_ids = set(self.names.reserved_keyword_ids)
        self.source_file = self.read_file()
        self.line_starts = [0] + [m.end() for m in re.finditer(r'\n', self.source_file)]

        self.token_specification = [
            ('COMMENT',       r'\#.*|\\\*[\s\S]*?\*\\'),
            ('WHITESPACE',    r'\s+'),
            ('STRING',        r'"[^"\n]*"'),
            ('NUMBER',        r'\d+'),
            ('NAME',          r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('SEMICOLON',     r';'),
            ('COLON',         r':'),
            ('EQUALS',        r'='),
            ('DOT',           r'\.'),
            ('INVALID',       r'.') 
        ]

        regex_string = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_specification)
        self.master_regex = re.compile(regex_string)

        self.token_iterator = self.master_regex.finditer(self.source_file)

    def print_error_line(self):
        try:
            print(f"Error on line {self.current_line}")
        except:
            raise Exception("Error finding current line when doing error ting - thign should never call idk why its hers")

    def read_file(self):
        """Return the source text, reading from the file if not supplied."""
        if self.source_text is not None:
            return self.source_text
        try:
            with open(self.path, "r") as file:
                return file.read()
        except (OSError, IOError):
            raise FileNotFoundError("The provided path was not found!")

    def get_symbol(self):
        """Fetch the next valid symbol, skipping whitespace and comments."""
        for match in self.token_iterator:
            kind = match.lastgroup
            start_index = match.span()[0]
            # if self.current_line < len(self.line_starts):
            #     if start_index >= self.line_starts[self.current_line]:
            #         self.current_line += 1

            while self.current_line < len(self.line_starts) and start_index >= self.line_starts[self.current_line]:
                self.current_line += 1

            value = match.group()
            
            if kind in ['WHITESPACE', 'COMMENT']:
                continue
                
            symbol = Symbol()
            symbol.id = self.names.lookup([value])[0]
            symbol.line = self.current_line

            if kind == 'NAME':
                if symbol.id in self.reserved_keyword_ids:
                    symbol.type = TokenType.KEYWORD
                else:
                    symbol.type = TokenType.NAME
                    
            elif kind == 'NUMBER':
                symbol.type = TokenType.NUMBER
                
            elif kind == 'STRING':
                symbol.type = TokenType.STRING
                
            elif kind == 'SEMICOLON':
                symbol.type = TokenType.SEMICOLON
                
            elif kind == 'COLON':
                symbol.type = TokenType.COLON
                
            elif kind == 'EQUALS':
                symbol.type = TokenType.EQUALS
                
            elif kind == 'DOT':
                symbol.type = TokenType.DOT
                
            else:
                symbol.type = TokenType.INVALID
                
            return symbol

        symbol = Symbol()
        symbol.type = TokenType.EOF
        return symbol
        
    def advance(self):
        """REDUNDANT - Read and return the next character in input_file.
        Need to write more tests and error correction codes"""
        try:
            return self.file.read(1)
        except Exception as e:
            raise Exception(f"Exception: {e}")

        
    def skip_whitespace_and_comments(self):
        """REDUNDANT - Skip spaces and comments."""
        while self.current_char:
            if self.current_char.isspace():
                self.advance()
            elif self.current_char == '#':
                while self.current_char and self.current_char != '\n':
                    self.advance()
            else:
                break

    def regexMatch(self, text):
        """REDUNDANT - can just use simple if blocks"""
        if not text:
            return TokenType.EOF

        number_regex = re.compile(r"^\d+")
        name_regex = re.compile(r"^[a-zA-Z0-9]+")
        
        colon_regex = re.compile(r"^\:")
        eol_regex = re.compile(r"^\;")
        dot_regex = re.compile(r"^\.")
        equals_regex = re.compile(r"^\=")
        string_regex = re.compile(r'^"[a-zA-Z0-9]+"') 

        if re.match(colon_regex, text):
            return TokenType.COLON
        elif re.match(eol_regex, text):
            return TokenType.SEMICOLON
        elif re.match(dot_regex, text):
            return TokenType.DOT
        elif re.match(equals_regex, text):
            return TokenType.EQUALS
        elif re.match(string_regex, text):
            return TokenType.STRING
        elif re.match(number_regex, text):
            return TokenType.NUMBER
        elif re.match(name_regex, text):
            return TokenType.NAME            
        return TokenType.INVALID