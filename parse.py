import os
from scanner import Scanner
from primativetypes import TokenType

"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
SubCircuitBlueprint - A structural template holding the uninstantiated layout of an imported file.
Parser - parses the definition file and builds the logic network.
"""
class SubCircuitBlueprint:
    """A structural template holding the uninstantiated layout of an imported file."""

    def __init__(self):
        # List of tuples: [(device_name_str, device_type_id, property_val), ...]
        self.devices = []
        # List of tuples: [(src_dev_str, src_port_str, dest_dev_str, dest_port_str), ...]
        self.connections = []

class Parser:

    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    parse_network(self): Parses the circuit definition file.
    """

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.scanner = scanner

        # Fetch the current starting symbol
        self.symbol = self.scanner.get_symbol()
        
        # Counter tracking syntax and semantic error tallies
        self.error_count = 0

        # Cache IDs for primitives
        self.primitive_keywords = [
            "SWITCH", "CLOCK", "AND", "OR", "NAND", "NOR", "XOR", "NOT", "DTYPE"
        ]
        self.primitive_ids = [self.names.query(kw) for kw in self.primitive_keywords]

        # Local registry for valid imports
        self.custom_types = {}


    def parse_network(self):
        """Parse the circuit definition file."""
        # Optional Imports Block
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("IMPORT"):
            self.parse_imports_block()
        
        # Mandatory Devices Block
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("DEVICES"):
            self.parse_devices_block()
        else:
            self.report_error("ERR_105", "Out-of-order block sequence structural arrangement declaration. Expected 'DEVICES:'.")

        # Mandatory Connections Block
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("CONNECT"):
            self.parse_connections_block()
        else:
            self.report_error("ERR_105", "Out-of-order block sequence structural arrangement declaration. Expected 'CONNECT:'.")

        # Mandatory Monitors Block
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("MONITOR"):
            self.parse_monitors_block()
        else:
            self.report_error("ERR_105", "Out-of-order block sequence structural arrangement declaration. Expected 'MONITOR:'.")
        
        # Global Document Terminator 'END'
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("END"):
            self.symbol = self.scanner.get_symbol()
            # If there is trailing data after the main END statement, flag it
            if self.symbol.type != TokenType.EOF:
                self.report_error("ERR_111", "Floating parameter token or syntax debris detected trailing statement lines.")
        else:
            if self.symbol.type == TokenType.EOF:
                self.report_error("ERR_101", "Unexpected end of file encountered before global 'END' sentinel.")
            else:
                self.report_error("ERR_111", "Floating parameter token or syntax debris detected trailing statement lines.")

        # Check for Open circuits only when no other errors are present
        if self.error_count == 0:
            if not self.network.check_network():
                self.report_error("ERR_220", "Open Circuit Warning. Network structural synthesis layout contains unconnected input gates.")

        return self.error_count == 0  # Return True if no errors were found, False otherwise
    
    def parse_imports_block(self):
        """Parse the optional macro declaration IMPORTS block."""
        import_id = self.names.query("IMPORT")
        end_id = self.names.query("END")

        self.symbol = self.scanner.get_symbol()  # Consume 'IMPORT'
        
        if self.symbol.type == TokenType.COLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_103", "Malformed block header. Expected a colon ':' following block declarations.")

        # Parse nested rules loop
        while self.symbol.type == TokenType.NAME:
            self.parse_import_rule()

        # Enforce explicit block terminator syntax: IMPORT END ;
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == import_id:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == TokenType.KEYWORD and self.symbol.id == end_id:
                self.symbol = self.scanner.get_symbol()
                if self.symbol.type == TokenType.SEMICOLON:
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            else:
                self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'IMPORT END' clause.")
        else:
            self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'IMPORT END' clause.")

    def parse_import_rule(self):
        """Parse an individual macro cross-file registration string rule."""
        custom_name_id = self.symbol.id
        custom_string = self.names.get_string(custom_name_id)

        # Semantic verification: Custom names cannot overwrite system primitives
        if custom_name_id in self.primitive_ids or custom_string in self.primitive_keywords:
            self.report_error("ERR_201", f"Illegal type definition: '{custom_string}' is a reserved primitive keyword.")
            self.panic_recover([self.scanner.SEMICOLON])
            return

        # Semantic verification: Check for duplicate macro bindings
        if custom_name_id in self.custom_types:
            self.report_error("ERR_202", f"Duplicate custom type path registration attempted for '{custom_string}'.")
            self.panic_recover([self.scanner.SEMICOLON])
            return

        self.symbol = self.scanner.get_symbol()

        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("FROM"):
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_108", "Missing file destination bridge operator. Expected 'FROM' keyword.")

        if self.symbol.type == TokenType.STRING:
            file_path_raw = self.names.get_string(self.symbol.id)
            # Normalize to clean string literals if scanner extracts literal raw quotes
            file_path_str = file_path_raw.strip('"\'')
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_109", "Malformed sub-circuit path string. Target file must be enclosed in double quotes.")
            file_path_str = None

        if self.symbol.type == TokenType.SEMICOLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_102", "Missing or misplaced termination character. Expected a semicolon ';'.")
            self.panic_recover([self.scanner.SEMICOLON, self.scanner.KEYWORD])

        # Execute recursive blueprint subcompilation if path tracking passed checks
        if file_path_str and self.error_count == 0:
            abs_path = os.path.abspath(file_path_str)
            if abs_path in self.active_import_paths:
                self.report_error("ERR_221", f"Circular dependency block encountered loading asset mapping: '{file_path_str}'.")
                return

            blueprint = self.compile_blueprint_file(abs_path)
            if blueprint:
                self.custom_types[custom_name_id] = blueprint
    
    def compile_blueprint_file(self, filepath):
        """Recursively instantiate isolated components to map out a file macro."""
        if not os.path.exists(filepath):
            self.report_error("ERR_203", f"Target custom macro path resource cannot be located: '{filepath}'.")
            return None

        sub_scanner = Scanner(filepath)
        sub_parser = Parser(self.names, self.devices, self.network, self.monitors, sub_scanner)
        
        sub_parser.custom_types = self.custom_types
        sub_parser.active_import_paths = self.active_import_paths + [filepath]
        sub_parser.is_blueprint_mode = True
        sub_parser.current_blueprint = SubCircuitBlueprint()

        success = sub_parser.parse_network()
        
        if not success or sub_parser.error_count > 0:
            self.report_error("ERR_204", f"Child macro file compilation aborted due to nested syntax or semantic errors in '{filepath}'.")
            self.error_count += sub_parser.error_count
            return None
            
        self.custom_types.update(sub_parser.custom_types)
        return sub_parser.current_blueprint
    
    def parse_devices_block(self):
        """Parse the mandatory Devices block."""
        # Implementation of device parsing logic goes here
        pass

    def parse_connections_block(self):
        """Parse the mandatory Connections block."""
        # Implementation of connection parsing logic goes here
        pass

    def parse_monitors_block(self):
        """Parse the mandatory Monitors block."""
        # Implementation of monitor parsing logic goes here
        pass

    def report_error(self, code_tag, specific_details=""):
        """Report an error with a specific code and message."""
        pass
    
    def panic_recover(self, stop_tokens):
        """Panic mode error recovery: skip symbols until a sync token is found."""
        pass