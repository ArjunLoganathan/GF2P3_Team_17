import pytest
from unittest.mock import MagicMock, patch, ANY
from primativetypes import TokenType
from parse import Parser, SubCircuitBlueprint

# Mock Dependencies)
@pytest.fixture
def mock_dependencies():
    """Provides mocked instances of all backend dependencies required by the Parser."""
    names = MagicMock()
    devices = MagicMock()
    network = MagicMock()
    monitors = MagicMock()
    scanner = MagicMock()
    
    # Configure default setup requirements
    names.query.side_effect = lambda kw: f"ID_{kw}"
    names.lookup.side_effect = lambda path_list: ["ID_" + p for p in path_list]

    devices.get_signal_ids.return_value = [99, 100]
    
    # Simulate first token returned by scanner
    initial_symbol = MagicMock()
    initial_symbol.type = TokenType.KEYWORD
    initial_symbol.id = "ID_DEVICES"
    scanner.get_symbol.return_value = initial_symbol
    
    return {
        "names": names,
        "devices": devices,
        "network": network,
        "monitors": monitors,
        "scanner": scanner
    }

@pytest.fixture
def parser(mock_dependencies):
    """Instantiates the Parser with mock objects."""
    return Parser(
        names=mock_dependencies["names"],
        devices=mock_dependencies["devices"],
        network=mock_dependencies["network"],
        monitors=mock_dependencies["monitors"],
        scanner=mock_dependencies["scanner"]
    )

# UNIT TESTS
def test_parser_initialization(parser, mock_dependencies):
    """Verifies that constants and tracking structures are correctly instantiated."""
    assert parser.error_count == 0
    assert parser.is_blueprint_mode is False
    assert parser.current_blueprint is None
    assert parser.symbol.id == "ID_DEVICES"
    mock_dependencies["scanner"].get_symbol.assert_called_once()


def test_report_error_increments_count(parser, capsys):
    """Ensures calling report_error increments the count and prints a formatted message."""
    assert parser.error_count == 0
    
    parser.report_error("ERR_102", "Expected a trailing semicolon ';'.")
    
    assert parser.error_count == 1
    captured = capsys.readouterr()
    assert "*** Error 102: Missing or misplaced character." in captured.out
    assert "Details: Expected a trailing semicolon ';'." in captured.out


def test_panic_recover(parser, mock_dependencies):
    """Validates that panic mode skips tokens until finding a synchronization token."""
    # Setup token sequences
    token_1 = MagicMock(type=TokenType.NAME)
    token_2 = MagicMock(type=TokenType.NUMBER)
    sync_token = MagicMock(type=TokenType.SEMICOLON)
    after_sync = MagicMock(type=TokenType.EOF)
    
    # Reset the parser's starting symbol so it actually enters the while loop
    parser.symbol = token_1
    mock_dependencies["scanner"].get_symbol.side_effect = [token_2, sync_token, after_sync]
    mock_dependencies["scanner"].get_symbol.call_count = 0 # Reset call tracker
    
    stop_set = {TokenType.SEMICOLON, TokenType.KEYWORD}
    parser.panic_recover(stop_set)
    
    # It should consume token_2, then sync_token, and then the token after the non-keyword sync token
    assert mock_dependencies["scanner"].get_symbol.call_count == 3
    assert parser.symbol == after_sync


# Semantic & Network tests
def test_resolve_and_connect_nodes_success(parser, mock_dependencies):
    """Checks a standard, successful node wiring handoff to the backend components."""
    mock_dependencies["devices"].get_device.return_value = MagicMock()
    mock_dependencies["network"].make_connection.return_value = parser.network.NO_ERROR
    
    with patch.object(parser, 'validate_macro_boundary_references', return_value=True), \
         patch.object(parser, 'trace_to_primitive_node', side_effect=[("G1", "I1"), ("G2", "I2")]):
         
        parser.resolve_and_connect_nodes("G1", "I1", "G2", "I2")
        
        mock_dependencies["network"].make_connection.assert_called_once()
        assert parser.error_count == 0


def test_resolve_and_connect_nodes_device_absent(parser, mock_dependencies):
    """Ensures ERR_211 triggers if a targeted device inside a routing rule is missing."""
    mock_dependencies["names"].query.return_value = None
    mock_dependencies["devices"].get_device.return_value = None
    
    with patch.object(parser, 'validate_macro_boundary_references', return_value=True), \
         patch.object(parser, 'report_error') as mock_report:
         
        parser.resolve_and_connect_nodes("G1", "I1", "G2", "I2")
        
        # Verify the specific error code was triggered
        mock_report.assert_called_once_with("ERR_211", ANY)


@pytest.mark.parametrize("net_error, expected_err_code", [
    ("INPUT_CONNECTED", "ERR_215"),
    ("DEVICE_ABSENT", "ERR_211"),
    ("PORT_ABSENT", "ERR_211"),
    ("INPUT_TO_INPUT", "ERR_216"),
    ("OUTPUT_TO_OUTPUT", "ERR_216"),
])
def test_resolve_and_connect_backend_errors(parser, mock_dependencies, net_error, expected_err_code):
    """Parametrized check confirming network backend error states register exact Parser error codes."""
    # Bypass lookup failures by providing truthy device IDs
    mock_dependencies["names"].query.return_value = 99
    if hasattr(parser.network, 'devices'):
        mock_dependencies["network"].devices.get_device_id.return_value = 99
    mock_dependencies["devices"].get_device.return_value = MagicMock()
    
    # Dynamically apply backend simulation variables 
    setattr(parser.network, net_error, net_error)
    setattr(parser.network, "NO_ERROR", "NO_ERROR")
    mock_dependencies["network"].make_connection.return_value = net_error
    
    with patch.object(parser, 'validate_macro_boundary_references', return_value=True), \
         patch.object(parser, 'report_error') as mock_report:
         
        parser.resolve_and_connect_nodes("G1", "I1", "G2", "I2")
        mock_report.assert_called_once_with(expected_err_code, ANY)


# COMPOSITE SIGNAL ROUTING PATHS
def test_parse_composite_signal_path_flat(parser, mock_dependencies):
    """Validates simple non-dotted structural references parse correctly."""
    token_name = MagicMock(type=TokenType.NAME, id="ID_G1")
    token_semi = MagicMock(type=TokenType.SEMICOLON)
    
    mock_dependencies["names"].get_string.return_value = "G1"
    mock_dependencies["scanner"].get_symbol.side_effect = [token_semi]
    
    parser.symbol = token_name
    dev_str, pin_str = parser.parse_composite_signal_path()
    
    assert dev_str == "G1"
    assert pin_str is None


def test_parse_composite_signal_path_dotted(parser, mock_dependencies):
    """Validates multi-tiered dotted path layouts (e.g. SubCircuit.Gate.Pin)."""
    token_sub = MagicMock(type=TokenType.NAME, id="ID_SUB")
    token_dot1 = MagicMock(type=TokenType.DOT)
    token_gate = MagicMock(type=TokenType.NAME, id="ID_G1")
    token_dot2 = MagicMock(type=TokenType.DOT)
    token_pin = MagicMock(type=TokenType.NAME, id="ID_I1")
    token_semi = MagicMock(type=TokenType.SEMICOLON)
    
    mock_dependencies["names"].get_string.side_effect = ["SUB", "G1", "I1"]
    mock_dependencies["scanner"].get_symbol.side_effect = [token_dot1, token_gate, token_dot2, token_pin, token_semi]
    
    parser.symbol = token_sub
    dev_str, pin_str = parser.parse_composite_signal_path()
    
    assert dev_str == "SUB.G1"
    assert pin_str == "I1"

def test_parse_composite_signal_path_invalid_token(parser, mock_dependencies):
    """Validates ERR_110 is triggered upon invalid token formatting."""
    # Simulate scanning a keyword where a NAME or NUMBER is expected
    token_invalid = MagicMock(type=TokenType.KEYWORD, id="ID_SOME_KEYWORD")
    parser.symbol = token_invalid
    
    with patch.object(parser, 'report_error') as mock_report:
        dev_str, pin_str = parser.parse_composite_signal_path()
        
        # Must gracefully return None and log ERR_110
        assert dev_str is None
        assert pin_str is None
        mock_report.assert_called_once_with("ERR_110", ANY)