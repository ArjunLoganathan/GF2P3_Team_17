"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""


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
        if self.symbol.type == self.scanner.KEYWORD and self.symbol.id == self.names.query("IMPORT"):
            self.parse_imports_block()
        
        # Mandatory Devices Block
        if self.symbol.type == self.scanner.KEYWORD and self.symbol.id == self.names.query("DEVICES"):
            self.parse_devices_block()
        else:
            self.report_error("ERR_105", "Missing mandatory 'DEVICES:' block header.")

        # Mandatory Connections Block
        if self.symbol.type == self.scanner.KEYWORD and self.symbol.id == self.names.query("CONNECT"):
            self.parse_connections_block()
        else:
            self.report_error("ERR_105", "Missing mandatory 'CONNECT:' block header.")
        
        # Mandatory Monitors Block
        if self.symbol.type == self.scanner.KEYWORD and self.symbol.id == self.names.query("MONITOR"):
            self.parse_monitors_block()
        else:
            self.report_error("ERR_105", "Missing mandatory 'MONITOR:' block header.")
        
        # Global Document Terminator 'END'
        if self.symbol.type == self.scanner.KEYWORD and self.symbol.id == self.names.query("END"):
            self.symbol = self.scanner.get_symbol()
            # Flag any trailing data after END 
            if self.symbol.type != self.scanner.EOF:
                self.report_error("ERR_111", "Extraneous data detected after the global 'END' file sentinel.")
        else:
            self.report_error("ERR_101", "Missing or misplaced global file terminator 'END'.")
        
        # Check for Open circuits only when no other errors are present
        if self.error_count == 0:
            if not self.network.check_network():
                self.report_error("ERR_220", "Critical Open Circuit Warning: Floating, unconnected inputs exist.")

        return self.error_count == 0  # Return True if no errors were found, False otherwise
    
    def parse_imports_block(self):
        """Parse the optional Imports block."""
        custom_name_id = self.symbol.id  # Cache the custom type name ID
        custom_name_str = self.names.get_string(custom_name_id)  # Get the string representation for error messages

        # Check for reserved primitive keyword conflicts
        if custom_name_id in self.primitive_ids or custom_name_str in self.primitive_keywords:
            self.report_error("ERR_201", f"Illegal type definition: '{custom_name_str}' is a reserved primitive keyword.")
            self.panic_recover([self.scanner.SEMICOLON])
            return
        
        # Check for duplicate custom type registrations
        if custom_name_id in self.custom_types:
            self.report_error("ERR_202", f"Duplicate custom type path registration attempted for '{custom_name_str}'.")
            self.panic_recover([self.scanner.SEMICOLON])
            return
        
        self.symbol = self.scanner.get_symbol()

        if self.symbol.type == self.scanner.KEYWORD and self.symbol.id == self.names.query("FROM"):
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_108", "Missing file destination bridge operator. Expected 'FROM' keyword.")

        if self.symbol.type == self.scanner.STRING:
            file_path_str = self.names.get_string(self.symbol.id)
            self.custom_types[custom_name_id] = file_path_str
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_109", "Malformed sub-circuit path string. Target file must be enclosed in double quotes.")

    
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