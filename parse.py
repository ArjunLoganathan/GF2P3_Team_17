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

        # Cache IDs for reserved system keywords/primitives to speed up parsing
        self.primitive_keywords = [
            "SWITCH", "CLOCK", "AND", "OR", "NAND", "NOR", "XOR", "NOT", "DTYPE"
        ]
        self.primitive_ids = [self.names.query(kw) for kw in self.primitive_keywords]

        # Local registry for valid imported sub-circuit macro bindings
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
