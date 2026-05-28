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
        self.input_ports = set()   # Set of input port identifiers for validation
        self.output_ports = set()  # Set of output port identifiers for validation

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

        # Macro flattening tracking structures
        self.custom_types = {}        # {type_name_id: SubCircuitBlueprint}
        self.instantiated_types = {}   # {instance_device_id_or_path_id: type_name_id}
        self.active_import_paths = []  # Dependency stack to catch circular recursion loops
        self.is_blueprint_mode = False # True if parsing an external file asset
        self.current_blueprint = None  # Reference to target template wrapper being built


    def parse_network(self):
        """Parse the circuit definition file. Contains Errors[101, 105, 111, 112, 113, 220]"""
        # Optional Imports Block
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("IMPORT"):
            self.parse_imports_block()
        
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("INPUT_PORTS"):
            self.parse_interface_ports_block(is_input=True)
        elif self.is_blueprint_mode:
            # Sub-circuit files MUST provide explicit entry boundary specifications
            self.report_error("ERR_112", "Missing or malformed 'INPUT_PORTS' declaration block in sub-circuit file.")

        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("OUTPUT_PORTS"):
            self.parse_interface_ports_block(is_input=False)
        elif self.is_blueprint_mode:
            # Sub-circuit files MUST provide explicit exit boundary specifications
            self.report_error("ERR_113", "Missing or malformed 'OUTPUT_PORTS' declaration block in sub-circuit file.")
            
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

        # Optional Monitors Block
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("MONITOR"):
            self.parse_monitors_block()
            
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
    
    def parse_interface_ports_block(self, is_input=True):
        """Parse INPUT_PORTS and OUTPUT_PORTS interface constraints for sub-circuit files. Contains Errors[102, 103, 104]"""
        block_kw_str = "INPUT_PORTS" if is_input else "OUTPUT_PORTS"
        block_id = self.names.query(block_kw_str)
        end_id = self.names.query("END")

        self.symbol = self.scanner.get_symbol() # Consume header keyword
        
        if self.symbol.type == TokenType.COLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_103", "Malformed block header. Expected a colon ':' following block declarations.")

        # Loop and pull signal pin name strings
        while self.symbol.type == TokenType.NAME:
            port_str = self.names.get_string(self.symbol.id)
            if is_input:
                self.current_blueprint.input_ports.add(port_str)
            else:
                self.current_blueprint.output_ports.add(port_str)
            
            self.symbol = self.scanner.get_symbol()
            
            if self.symbol.type == TokenType.SEMICOLON:
                self.symbol = self.scanner.get_symbol()
            else:
                self.report_error("ERR_102", f"Missing or misplaced character. Expected a trailing semicolon ';' after port '{port_str}'.")
                self.panic_recover([TokenType.SEMICOLON, TokenType.KEYWORD])

        # Enforce formal structural closure parsing rules
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == block_id:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == TokenType.KEYWORD and self.symbol.id == end_id:
                self.symbol = self.scanner.get_symbol()
                if self.symbol.type == TokenType.SEMICOLON:
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            else:
                self.report_error("ERR_104", f"Block termination mismatch. Missing or malformed '{block_kw_str} END' clause.")
        else:
            self.report_error("ERR_104", f"Block termination mismatch. Missing or malformed '{block_kw_str} END' clause.")

    def resolve_and_connect_nodes(self, src_dev_path, src_port, dest_dev_path, dest_port):
        """Trace macro interface connection chains and validate interface alignment constraints.
        Contains Errors[211, 212, 213, 215, 216]"""
        
        # ensure the port references actually exist and aren't directionally flipped.
        if not self.validate_macro_boundary_references(src_dev_path, src_port, expect_input=False):
            return
        if not self.validate_macro_boundary_references(dest_dev_path, dest_port, expect_input=True):
            return

        final_src_dev, final_src_port = self.trace_to_primitive_node(src_dev_path, src_port)
        final_dest_dev, final_dest_port = self.trace_to_primitive_node(dest_dev_path, dest_port)

        src_signal_str = f"{final_src_dev}.{final_src_port}" if final_src_port else final_src_dev
        dest_signal_str = f"{final_dest_dev}.{final_dest_port}" if final_dest_port else final_dest_dev

        [src_id, src_port_id] = self.devices.get_signal_ids(src_signal_str)
        [dest_id, dest_port_id] = self.devices.get_signal_ids(dest_signal_str)

        if self.devices.get_device(src_id) is None or self.devices.get_device(dest_id) is None:
            self.report_error("ERR_211", f"Unresolved line routing assignment. Device identifier referenced was never initialized.")
            return

        net_error = self.network.make_connection(src_id, src_port_id, dest_id, dest_port_id)
        if net_error != self.network.NO_ERROR:
            if net_error == self.network.INPUT_CONNECTED:
                self.report_error("ERR_215", f"Port fan-in constraint violation. Target input pin port already driven by an output source.")
            elif net_error in [self.network.DEVICE_ABSENT, self.network.PORT_ABSENT]:
                self.report_error("ERR_211", f"Unresolved line routing assignment or invalid port mapping.")
            elif net_error in [self.network.INPUT_TO_INPUT, self.network.OUTPUT_TO_OUTPUT]:
                self.report_error("ERR_216", f"Directional typing error. Signal linkages must traverse strictly from Output to Input ports.")
            
    def validate_macro_boundary_references(self, dev_path, port_name, expect_input=True):
        """Scan connection assignments to catch ERR_222 and ERR_217 interface boundary violations.
        Contains Errors[214, 217, 222]"""
        parts = dev_path.split(".")
        current_scope = ""
        
        for i, part in enumerate(parts):
            current_scope = f"{current_scope}.{part}" if current_scope else part
            scope_id = self.names.lookup([current_scope])[0]
            
            # If this path step belongs to an instantiated Macro Type template
            if scope_id in self.instantiated_types:
                macro_type_id = self.instantiated_types[scope_id]
                blueprint = self.custom_types[macro_type_id]
                
                # If there are no trailing path steps, the referenced pin is directly on this macro's shell
                if i == len(parts) - 1:
                    if not port_name:
                        self.report_error("ERR_214", f"Missing terminal pin qualifier.")
                        return False
                        
                    is_in_set = port_name in blueprint.input_ports
                    is_out_set = port_name in blueprint.output_ports
                    
                    # Check if the port exists on the boundary declaration (ERR_222)
                    if not is_in_set and not is_out_set:
                        self.report_error("ERR_222", f"Interface boundary mismatch. Port referenced in main layout does not exist on imported macro. Pin: '{port_name}'")
                        return False
                    
                    # Check if the directionality matches the connection wire alignment intent (ERR_217)
                    if expect_input and is_out_set:
                        self.report_error("ERR_217", f"Macro interface typing mismatch. Child input/output port directionality has been flipped. Port: '{port_name}'")
                        return False
                    elif not expect_input and is_in_set:
                        self.report_error("ERR_217", f"Macro interface typing mismatch. Child input/output port directionality has been flipped. Port: '{port_name}'")
                        return False
        return True
    
    def parse_imports_block(self):
        """Parse the optional macro declaration IMPORTS block. Contains Errors[102, 103, 104]"""
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
        """Parse an individual macro cross-file registration string rule. Contains Errors[102, 108, 109, 201, 202, 221]"""
        custom_name_id = self.symbol.id
        custom_string = self.names.get_string(custom_name_id)

        # Semantic verification: Custom names cannot overwrite system primitives
        if custom_name_id in self.primitive_ids or custom_string in self.primitive_keywords:
            self.report_error("ERR_201", f"Illegal type definition. Custom names cannot overwrite system primitives. Key: '{custom_string}'")
            self.panic_recover([TokenType.SEMICOLON])
            return

        # Semantic verification: Check for duplicate macro bindings
        if custom_name_id in self.custom_types:
            self.report_error("ERR_202", f"Duplicate custom type import registration path attempted for '{custom_string}'.")
            self.panic_recover([TokenType.SEMICOLON])
            return

        self.symbol = self.scanner.get_symbol()

        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == self.names.query("FROM"):
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_108", "Missing file mapping path assignment direction. Expected 'FROM' keyword.")

        if self.symbol.type == TokenType.STRING:
            file_path_raw = self.names.get_string(self.symbol.id)
            file_path_str = file_path_raw.strip('"\'')
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_109", "Malformed character string. Paths must be wrapped in matching double quotes '\"'.")
            file_path_str = None

        if self.symbol.type == TokenType.SEMICOLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            self.panic_recover([TokenType.SEMICOLON, TokenType.KEYWORD])

        # Execute recursive blueprint sub-compilation if path tracking passed checks
        if file_path_str and self.error_count == 0:
            abs_path = os.path.abspath(file_path_str)
            if abs_path in self.active_import_paths:
                self.report_error("ERR_221", f"Circular dependency chain detected in file import statements for: '{file_path_str}'.")
                return

            blueprint = self.compile_blueprint_file(abs_path)
            if blueprint:
                self.custom_types[custom_name_id] = blueprint
    
    def compile_blueprint_file(self, filepath):
        """Recursively instantiate isolated components to map out a file macro. Contains Errors[203, 204]"""
        if not os.path.exists(filepath):
            self.report_error("ERR_203", f"Target custom macro path resource cannot be located: '{filepath}'.")
            return None

        sub_scanner = Scanner(filepath, self.names)
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
        """Parse the mandatory Devices block. Contains Errors[102, 103, 104]"""
        devices_id = self.names.query("DEVICES")
        end_id = self.names.query("END")

        self.symbol = self.scanner.get_symbol()  # Consume 'DEVICES'
        
        if self.symbol.type == TokenType.COLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_103", "Malformed block header. Expected a colon ':' following block declarations.")

        while self.symbol.type == TokenType.NAME:
            self.parse_device_declaration()

        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == devices_id:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == TokenType.KEYWORD and self.symbol.id == end_id:
                self.symbol = self.scanner.get_symbol()
                if self.symbol.type == TokenType.SEMICOLON:
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            else:
                self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'DEVICES END' clause.")
        else:
            self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'DEVICES END' clause.")

    def parse_device_declaration(self, prefix=""):
        """Instantiate logic device modules onto the internal simulator structure engine. Contains Errors[102, 106, 107, 110, 205, 206, 207, 208, 209, 210]"""
        device_name_id = self.symbol.id
        device_name_str = self.names.get_string(device_name_id)
        
        scoped_name_str = f"{prefix}.{device_name_str}" if prefix else device_name_str
        scoped_name_id = self.names.lookup([scoped_name_str])[0]
        
        self.symbol = self.scanner.get_symbol()

        if self.symbol.type == TokenType.EQUALS:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_106", f"Missing or invalid assignment symbol. Expected '=' operator on '{device_name_str}'.")

        device_type_id = None
        is_primitive = False

        if self.symbol.type == TokenType.KEYWORD and self.symbol.id in self.primitive_ids:
            device_type_id = self.symbol.id
            is_primitive = True
            self.symbol = self.scanner.get_symbol()
        elif self.symbol.type == TokenType.NAME and self.symbol.id in self.custom_types:
            device_type_id = self.symbol.id
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_206", f"Unknown or unregistered device type configuration identifier mapping: '{device_name_str}'.")
            self.panic_recover([TokenType.SEMICOLON])
            return

        parameter_val = None
        if self.symbol.type == TokenType.NUMBER:
            parameter_val = int(self.names.get_string(self.symbol.id))
            self.symbol = self.scanner.get_symbol()
            if not is_primitive:
                self.report_error("ERR_210", f"Extraneous parameter passed. Primitives like XOR, NOT, and DTYPE do not accept arguments. (Or custom macro '{device_name_str}')")
        else:
            # Enforce required parameters for structural primitives that expect them
            if is_primitive:
                type_str = self.names.get_string(device_type_id)
                if type_str in ["SWITCH", "CLOCK", "AND", "OR", "NAND", "NOR"]:
                    self.report_error("ERR_107", "Expected a valid device parameter or configuration state integer.")

        if self.error_count == 0:
            if self.is_blueprint_mode:
                self.current_blueprint.devices.append((device_name_str, device_type_id, parameter_val))
            else:
                if not is_primitive:
                    self.instantiated_types[scoped_name_id] = device_type_id
                    self.flatten_macro_to_hardware(scoped_name_str, device_type_id)
                else:
                    type_str = self.names.get_string(device_type_id)
                    
                    if type_str == "SWITCH" and (parameter_val is None or parameter_val not in [0, 1]):
                        self.report_error("ERR_208", f"Invalid initialization properties. SWITCH types must map to absolute binary 0 or 1 on '{device_name_str}'.")
                    elif type_str == "CLOCK" and (parameter_val is None or parameter_val <= 0):
                        self.report_error("ERR_209", f"Invalid timing parameter properties. CLOCK frequencies must be positive non-zero integers on '{device_name_str}'.")
                    elif type_str in ["AND", "OR", "NAND", "NOR"] and (parameter_val is None or not (1 <= parameter_val <= 16)):
                        self.report_error("ERR_207", f"Component pin allocation constraints out-of-bounds. Primitives require 1-16 inputs on '{device_name_str}'.")
                    elif type_str in ["XOR", "NOT", "DTYPE"] and parameter_val is not None:
                        self.report_error("ERR_210", f"Extraneous parameter passed. Primitives like XOR, NOT, and DTYPE do not accept arguments.")

                    make_error = self.devices.make_device(scoped_name_id, device_type_id, parameter_val)
                    if make_error != self.devices.NO_ERROR:
                        if make_error == self.devices.DEVICE_PRESENT:
                            self.report_error("ERR_205", f"Duplicate component instance declaration. Device string identifier already active: '{device_name_str}'.")
                        else:
                            self.report_error("ERR_110", f"Invalid alphanumeric token layout format intercepted by Lexical Scanner during initialization of '{device_name_str}'.")

        if self.symbol.type == TokenType.SEMICOLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_102", f"Missing or misplaced character. Expected a trailing semicolon ';' at the end of declaration for '{device_name_str}'.")
            self.panic_recover([TokenType.SEMICOLON, TokenType.KEYWORD])

    def flatten_macro_to_hardware(self, instance_prefix, type_id):
        """Unroll macro blueprints down into flat primitive hardware elements recursively."""
        macro_blueprint = self.custom_types[type_id]

        for inner_dev_name, inner_type_id, inner_prop in macro_blueprint.devices:
            combined_name_str = f"{instance_prefix}.{inner_dev_name}"
            combined_name_id = self.names.lookup([combined_name_str])[0]
            
            if inner_type_id in self.custom_types:
                self.instantiated_types[combined_name_id] = inner_type_id
                self.flatten_macro_to_hardware(combined_name_str, inner_type_id)
            else:
                self.devices.make_device(combined_name_id, inner_type_id, inner_prop)

        for src_dev, src_p, dest_dev, dest_p in macro_blueprint.connections:
            flat_src_dev = f"{instance_prefix}.{src_dev}"
            flat_dest_dev = f"{instance_prefix}.{dest_dev}"
            self.resolve_and_connect_nodes(flat_src_dev, src_p, flat_dest_dev, dest_p)

    def parse_connections_block(self):
        """Parse the wiring route interconnections block configurations.
        Contains Errors[102, 103, 104]"""
        connect_id = self.names.query("CONNECT")
        end_id = self.names.query("END")
        self.symbol = self.scanner.get_symbol()
        if self.symbol.type == TokenType.COLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_103", "Malformed block header. Expected a colon ':' following block declarations.")
        while self.symbol.type == TokenType.NAME:
            self.parse_connection_rule()
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == connect_id:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == TokenType.KEYWORD and self.symbol.id == end_id:
                self.symbol = self.scanner.get_symbol()
                if self.symbol.type == TokenType.SEMICOLON:
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            else:
                self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'CONNECT END' clause.")
        else:
            self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'CONNECT END' clause.")
    
    def parse_connection_rule(self):
        """Parse an individual connection rule. Contains Errors[102, 106]"""
        out_dev_str, out_pin_str = self.parse_composite_signal_path()

        if self.symbol.type == TokenType.EQUALS:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_106", "Missing or invalid assignment symbol. Expected '=' operator.")

        in_dev_str, in_pin_str = self.parse_composite_signal_path()

        if self.error_count == 0 and out_dev_str and in_dev_str:
            if self.is_blueprint_mode:
                self.current_blueprint.connections.append((out_dev_str, out_pin_str, in_dev_str, in_pin_str))
            else:
                self.resolve_and_connect_nodes(out_dev_str, out_pin_str, in_dev_str, in_pin_str)

        if self.symbol.type == TokenType.SEMICOLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            self.panic_recover([TokenType.SEMICOLON, TokenType.KEYWORD])

    def parse_composite_signal_path(self):
        """Extract flat or multidot namespace path chains. Contains Errors[110]"""
        segments = []
        while True:
            if self.symbol.type not in [TokenType.NAME, TokenType.NUMBER]:
                self.report_error("ERR_110", "Invalid alphanumeric token layout format intercepted by Lexical Scanner.")
                return None, None
            
            segments.append(self.names.get_string(self.symbol.id))
            self.symbol = self.scanner.get_symbol()
            
            if self.symbol.type == TokenType.DOT:
                self.symbol = self.scanner.get_symbol()
                continue
            break

        if len(segments) == 1:
            return segments[0], None
        else:
            return ".".join(segments[:-1]), segments[-1]
    
    def resolve_and_connect_nodes(self, src_dev_path, src_port, dest_dev_path, dest_port):
        """Trace macro interface connection chains to link inner primitive paths directly. Contains Errors[211, 215]"""
        final_src_dev, final_src_port = self.trace_to_primitive_node(src_dev_path, src_port)
        final_dest_dev, final_dest_port = self.trace_to_primitive_node(dest_dev_path, dest_port)

        src_id = self.network.devices.get_device_id(final_src_dev) if hasattr(self.network.devices, 'get_device_id') else self.names.query(final_src_dev)
        dest_id = self.network.devices.get_device_id(final_dest_dev) if hasattr(self.network.devices, 'get_device_id') else self.names.query(final_dest_dev)
        
        if not src_id or not dest_id:
            self.report_error("ERR_211", f"Unresolved line routing assignment. Device identifier referenced was never initialized.")
            return

        src_port_id = self.names.query(final_src_port) if final_src_port else None
        dest_port_id = self.names.query(final_dest_port) if final_dest_port else None

        net_error = self.network.make_connection(src_id, src_port_id, dest_id, dest_port_id)
        if net_error != self.network.NO_ERROR:
            if net_error == self.network.INPUT_CONNECTED:
                self.report_error("ERR_215", f"Port fan-in constraint violation. Target input pin port already driven by an output source.")
            elif net_error in [self.network.DEVICE_ABSENT, self.network.PORT_ABSENT]:
                self.report_error("ERR_211", f"Unresolved port or routing element mapping missing from target.")

    def trace_to_primitive_node(self, dev_path, initial_port):
        """Traverse structural container path steps to expose the inner flat target primitive node."""
        parts = dev_path.split(".")
        current_scope = ""
        
        for i, part in enumerate(parts):
            current_scope = f"{current_scope}.{part}" if current_scope else part
            scope_id = self.names.lookup([current_scope])[0]
            
            if scope_id in self.instantiated_types:
                macro_type_id = self.instantiated_types[scope_id]
                blueprint = self.custom_types[macro_type_id]
                
                remaining_path = ".".join(parts[i+1:])
                internal_target_dev = f"{current_scope}.{remaining_path}" if remaining_path else current_scope
                return internal_target_dev, initial_port

        return dev_path, initial_port
    
    def parse_signal_path(self, is_input_rule=False):
        """Parse flat labels or compound path extensions using dot notation parsing.
        Contains Errors[110, 211, 214]"""
        dev_id = self.symbol.id
        dev_str = self.names.get_string(dev_id)
        pin_id = None
        self.symbol = self.scanner.get_symbol()
        if self.symbol.type == TokenType.DOT:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type in [TokenType.NAME, TokenType.NUMBER]:
                pin_id = self.symbol.id
                self.symbol = self.scanner.get_symbol()
            else:
                self.report_error("ERR_110", "Invalid alphanumeric token layout format intercepted by Lexical Scanner.")
        else:
            if self.error_count == 0:
                dev_instance = self.devices.get_device(dev_id)
                if not dev_instance:
                    self.report_error("ERR_211", f"Unresolved line routing assignment. Device identifier referenced was never initialized '{dev_str}'.")
                elif dev_instance.device_kind == self.devices.D_TYPE:
                    self.report_error("ERR_214", f"Missing terminal pin qualifier. Primitives or macro blocks require explicit dot syntax on DTYPE node '{dev_str}'.")
                elif is_input_rule:
                    self.report_error("ERR_214", f"Missing terminal pin qualifier. Primitives or macro blocks require explicit dot syntax on '{dev_str}'.")
        return dev_id, pin_id
    
    def parse_monitors_block(self):
        """Parse the optional Monitors block."""
        monitor_id = self.names.query("MONITOR")
        end_id = self.names.query("END")
        self.symbol = self.scanner.get_symbol()
        if self.symbol.type == TokenType.COLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_103", "Malformed block header. Expected a colon ':' following block declarations.")
        while self.symbol.type == TokenType.NAME:
            self.parse_monitor_rule()
        if self.symbol.type == TokenType.KEYWORD and self.symbol.id == monitor_id:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == TokenType.KEYWORD and self.symbol.id == end_id:
                self.symbol = self.scanner.get_symbol()
                if self.symbol.type == TokenType.SEMICOLON:
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.report_error("ERR_102", "Missing or misplaced character. Expected a trailing semicolon ';'.")
            else:
                self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'MONITOR END' clause.")
        else:
            self.report_error("ERR_104", "Block termination mismatch. Missing or malformed 'MONITOR END' clause.")
    
    def parse_monitor_rule(self):
        """Parse an individual monitor rule."""
        dev_path_str, pin_str = self.parse_composite_signal_path()
        if self.error_count == 0 and dev_path_str:
            final_dev_str, final_pin_str = self.trace_to_primitive_node(dev_path_str, pin_str)
            dev_id = self.names.lookup([final_dev_str])[0]
            pin_id = self.names.lookup([final_pin_str])[0] if final_pin_str else None
            mon_error = self.monitors.make_monitor(dev_id, pin_id)
            if mon_error != self.monitors.NO_ERROR:
                if mon_error == self.monitors.NOT_OUTPUT:
                    self.report_error("ERR_218", f"Cannot track diagnostics trace loop target. Component node is not a valid output line on '{final_dev_str}'.")
                elif mon_error == self.monitors.MONITOR_PRESENT:
                    self.report_error("ERR_219", f"Duplicate monitor trace instruction targeting identical terminal routes on '{final_dev_str}'.")
        if self.symbol.type == TokenType.SEMICOLON:
            self.symbol = self.scanner.get_symbol()
        else:
            self.report_error("ERR_102", f"Missing or misplaced character. Expected a trailing semicolon ';' for monitor config on '{dev_path_str}'.")
            self.panic_recover([TokenType.SEMICOLON, TokenType.KEYWORD])

    def report_error(self, code_tag, specific_details=""):
        """Report an error with a specific code and message."""
        self.error_count += 1
        error_messages = {
            "ERR_101": "Error 101: Unexpected end of file encountered before global 'END' sentinel.",
            "ERR_102": "Error 102: Missing or misplaced character. Expected a trailing semicolon ';'.",
            "ERR_103": "Error 103: Malformed block header. Expected a colon ':' following block declarations.",
            "ERR_104": "Error 104: Block termination mismatch. Missing or malformed '<BLOCKNAME> END' clause.",
            "ERR_105": "Error 105: Out-of-order block sequence structural arrangement declaration.",
            "ERR_106": "Error 106: Missing or invalid assignment symbol. Expected '=' operator.",
            "ERR_107": "Error 107: Expected a valid device parameter or configuration state integer.",
            "ERR_108": "Error 108: Missing file mapping path assignment direction. Expected 'FROM' keyword.",
            "ERR_109": "Error 109: Malformed character string. Paths must be wrapped in matching double quotes '\"'.",
            "ERR_110": "Error 110: Invalid alphanumeric token layout format intercepted by Lexical Scanner.",
            "ERR_111": "Error 111: Floating parameter token or syntax debris detected trailing statement lines.",
            "ERR_112": "Error 112: Missing or malformed 'INPUT_PORTS' declaration block in sub-circuit file.",
            "ERR_113": "Error 113: Missing or malformed 'OUTPUT_PORTS' declaration block in sub-circuit file.",
            "ERR_201": "Error 201: Illegal type definition. Custom names cannot overwrite system primitives.",
            "ERR_202": "Error 202: Duplicate custom type import registration path attempted.",
            "ERR_203": "Error 203: Target blueprint layout file path could not be resolved by the workspace.",
            "ERR_204": "Error 204: Child macro file compilation aborted due to nested syntax or semantic errors.",
            "ERR_205": "Error 205: Duplicate component instance declaration. Device string identifier already active.",
            "ERR_206": "Error 206: Unknown or unregistered device type configuration identifier mapping.",
            "ERR_207": "Error 207: Component pin allocation constraints out-of-bounds. Primitives require 1-16 inputs.",
            "ERR_208": "Error 208: Invalid initialization properties. SWITCH types must map to absolute binary 0 or 1.",
            "ERR_209": "Error 209: Invalid timing parameter properties. CLOCK frequencies must be positive non-zero integers.",
            "ERR_210": "Error 210: Extraneous parameter passed. Primitives like XOR, NOT, and DTYPE do not accept arguments.",
            "ERR_211": "Error 211: Unresolved line routing assignment. Device identifier referenced was never initialized.",
            "ERR_212": "Error 212: Invalid input port identifier. Pin does not exist on this component type.",
            "ERR_213": "Error 213: Invalid output port identifier. Pin does not exist on this component type.",
            "ERR_214": "Error 214: Missing terminal pin qualifier. Primitives or macro blocks require explicit dot syntax.",
            "ERR_215": "Error 215: Port fan-in constraint violation. Target input pin port already driven by an output source.",
            "ERR_216": "Error 216: Directional typing error. Signal linkages must traverse strictly from Output to Input ports.",
            "ERR_217": "Error 217: Macro interface typing mismatch. Child input/output port directionality has been flipped.",
            "ERR_218": "Error 218: Cannot track diagnostics trace loop target. Component node is not a valid output line.",
            "ERR_219": "Error 219: Duplicate monitor trace instruction targeting identical terminal routes.",
            "ERR_220": "Error 220: Open Circuit Warning. Network structural synthesis layout contains unconnected input gates.",
            "ERR_221": "Error 221: Circular dependency chain detected in file import statements.",
            "ERR_222": "Error 222: Interface boundary mismatch. Port referenced in main layout does not exist on imported macro."
        }
        if hasattr(self.scanner, 'print_error_line'):
            self.scanner.print_error_line()
        base_msg = error_messages.get(code_tag, f"Unknown Error Condition [{code_tag}].")
        if specific_details:
            print(f"*** {base_msg} Details: {specific_details}\n")
        else:
            print(f"*** {base_msg}\n")
    
    def panic_recover(self, stop_tokens):
        """Panic mode error recovery: skip symbols until a sync token is found."""
        while self.symbol.type not in stop_tokens and self.symbol.type != TokenType.EOF:
            self.symbol = self.scanner.get_symbol()
        if self.symbol.type in stop_tokens and self.symbol.type != TokenType.KEYWORD:
            self.symbol = self.scanner.get_symbol() 