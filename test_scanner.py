import pytest
from scanner import Scanner, Symbol
from primativetypes import TokenType
from names import Names

'''
Probably best if more tests are written but I'm unsure what else needs to be tested for the scanner. 
Perhaps write full files to test but that should be parsers job.
'''

@pytest.fixture
def names_instance():
    return Names()

def write_and_scan(tmp_path, text, names):
    """Helper to write text to a temp file and return a scanner instance."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text(text)
    return Scanner(str(test_file), names)

def test_scanner_file_not_found(names_instance):
    """Test that an invalid path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        Scanner("non_existent_file.txt", names_instance)

def test_scanner_eof(tmp_path, names_instance):
    """Test that an empty file immediately returns EOF."""
    scanner = write_and_scan(tmp_path, "", names_instance)
    symbol = scanner.get_symbol()
    assert symbol.type == TokenType.EOF

def test_scanner_keywords_and_names(tmp_path, names_instance):
    """Test that keywords and names are distinguished properly."""
    text = "DEVICES MyGate1"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    sym1 = scanner.get_symbol()
    assert sym1.type == TokenType.KEYWORD
    assert names_instance.get_name_string(sym1.id) == "DEVICES"
    
    sym2 = scanner.get_symbol()
    assert sym2.type == TokenType.NAME
    assert names_instance.get_name_string(sym2.id) == "MyGate1"
    
    assert scanner.get_symbol().type == TokenType.EOF

def test_scanner_punctuation(tmp_path, names_instance):
    """Test that punctuation is parsed into the correct TokenTypes."""
    text = "G1.1 = 0;"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    assert scanner.get_symbol().type == TokenType.NAME
    assert scanner.get_symbol().type == TokenType.DOT
    assert scanner.get_symbol().type == TokenType.NUMBER
    assert scanner.get_symbol().type == TokenType.EQUALS
    assert scanner.get_symbol().type == TokenType.NUMBER
    assert scanner.get_symbol().type == TokenType.SEMICOLON
    assert scanner.get_symbol().type == TokenType.EOF

def test_scanner_comments(tmp_path, names_instance):
    """Test that comments are entirely ignored."""
    text = "# This is a comment\nCONNECT:"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    sym = scanner.get_symbol()
    assert sym.type == TokenType.KEYWORD
    assert names_instance.get_name_string(sym.id) == "CONNECT"

def test_scanner_strings(tmp_path, names_instance):
    """Test that double-quoted strings are parsed as TokenType.STRING."""
    text = 'IMPORT: "adder.txt";'
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    assert scanner.get_symbol().type == TokenType.KEYWORD
    assert scanner.get_symbol().type == TokenType.COLON
    sym = scanner.get_symbol()
    assert sym.type == TokenType.STRING
    assert names_instance.get_name_string(sym.id) == '"adder.txt"'

def test_scanner_block_comments(tmp_path, names_instance):
    r"""Test that multi-line block comments \* ... *\ are ignored."""
    text = "DEVICES\n\\* This is a\nmulti-line comment *\\\nCONNECT"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    sym1 = scanner.get_symbol()
    assert sym1.type == TokenType.KEYWORD
    assert names_instance.get_name_string(sym1.id) == "DEVICES"
    assert sym1.line == 1
    
    sym2 = scanner.get_symbol()
    assert sym2.type == TokenType.KEYWORD
    assert names_instance.get_name_string(sym2.id) == "CONNECT"
    assert sym2.line == 4

def test_scanner_line_number_tracking(tmp_path, names_instance):
    """Test that the scanner accurately tracks line numbers."""
    text = "G1.1\n\n\n=\n0;"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    sym1 = scanner.get_symbol() # G1
    assert sym1.line == 1
    scanner.get_symbol() # .
    scanner.get_symbol() # 1
    
    sym4 = scanner.get_symbol() # =
    assert sym4.line == 4
    
    sym5 = scanner.get_symbol() # 0
    assert sym5.line == 5

def test_scanner_invalid_character(tmp_path, names_instance):
    """Test that illegal characters return TokenType.INVALID."""
    text = "G1.1 $ 0;"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    scanner.get_symbol() # G1
    scanner.get_symbol() # .
    scanner.get_symbol() # 1
    
    invalid_sym = scanner.get_symbol() # $
    assert invalid_sym.type == TokenType.INVALID

def test_scanner_print_error_line(tmp_path, names_instance, capsys):
    """Test that the error printer outputs the line and a caret ^ at the right column."""
    text = "CONNECT:\nG1.1 $ 0;\nMONITOR:"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    for _ in range(6):
        sym = scanner.get_symbol()
        
    assert sym.type == TokenType.INVALID
    
    scanner.print_error_line()
    
    captured = capsys.readouterr()
    output_lines = captured.out.split('\n')

    assert "G1.1 $ 0;" in output_lines[1]
    assert "     ^" in output_lines[2]