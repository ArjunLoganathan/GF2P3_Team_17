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

def test_scanner_unterminated_string(tmp_path, names_instance):
    """Test that missing closing quotes yield INVALID tokens, not crashes."""
    text = 'IMPORT: "adder.txt ;' 
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    assert scanner.get_symbol().type == TokenType.KEYWORD
    assert scanner.get_symbol().type == TokenType.COLON
    
    invalid_sym = scanner.get_symbol()
    assert invalid_sym.type == TokenType.INVALID
    
    name_sym = scanner.get_symbol()
    assert name_sym.type == TokenType.NAME
    assert names_instance.get_name_string(name_sym.id) == "adder"

def test_scanner_unterminated_block_comment(tmp_path, names_instance):
    r"""Test that an unclosed \* block comment results in INVALID tokens."""
    text = "DEVICES:\n\\* Forgot to close this comment\nCONNECT:"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    assert scanner.get_symbol().type == TokenType.KEYWORD
    assert scanner.get_symbol().type == TokenType.COLON
    
    assert scanner.get_symbol().type == TokenType.INVALID
    assert scanner.get_symbol().type == TokenType.INVALID

def test_scanner_name_starting_with_number(tmp_path, names_instance):
    """Test that numbers glued to names are split into NUMBER and NAME."""
    text = "123GATE"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    num_sym = scanner.get_symbol()
    assert num_sym.type == TokenType.NUMBER
    
    name_sym = scanner.get_symbol()
    assert name_sym.type == TokenType.NAME
    assert names_instance.get_name_string(name_sym.id) == "GATE"

def test_scanner_consecutive_invalid_chars(tmp_path, names_instance):
    """Test that multiple illegal characters return multiple INVALID tokens."""
    text = "$$@"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    assert scanner.get_symbol().type == TokenType.INVALID
    assert scanner.get_symbol().type == TokenType.INVALID
    assert scanner.get_symbol().type == TokenType.INVALID
    assert scanner.get_symbol().type == TokenType.EOF

def test_scanner_trailing_whitespace_and_comments_no_newline(tmp_path, names_instance):
    """Test EOF detection when the file ends with spaces or a comment, no newline."""
    text = "G1.1 = 0;   # Final comment without a newline at the end"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    assert scanner.get_symbol().type == TokenType.NAME
    assert scanner.get_symbol().type == TokenType.DOT
    assert scanner.get_symbol().type == TokenType.NUMBER
    assert scanner.get_symbol().type == TokenType.EQUALS
    assert scanner.get_symbol().type == TokenType.NUMBER
    assert scanner.get_symbol().type == TokenType.SEMICOLON
    
    assert scanner.get_symbol().type == TokenType.EOF

def test_scanner_with_source_text_directly(names_instance):
    """Test that the scanner can accept source text directly without reading from a file path."""
    # Passing a dummy path because source_text overrides file reading
    scanner = Scanner(path="dummy_path.txt", names=names_instance, source_text="DEVICES;")
    
    assert scanner.get_symbol().type == TokenType.KEYWORD
    assert scanner.get_symbol().type == TokenType.SEMICOLON
    assert scanner.get_symbol().type == TokenType.EOF

def test_scanner_print_error_last_line_no_newline(tmp_path, names_instance, capsys):
    """Test print_error_line when the error occurs on the final line with no trailing newline."""
    text = "DEVICES\nINVALID_TOKEN $"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    # Step through tokens to reach the invalid symbol '$'
    scanner.get_symbol()  # DEVICES
    scanner.get_symbol()  # INVALID_TOKEN
    invalid_sym = scanner.get_symbol()  # $
    assert invalid_sym.type == TokenType.INVALID
    
    scanner.print_error_line()
    
    captured = capsys.readouterr()
    output_lines = captured.out.split('\n')
    
    # Verify the visual caret points exactly to the '$' character
    assert "INVALID_TOKEN $" in output_lines[1]
    assert "              ^" in output_lines[2]

def test_scanner_print_error_with_explicit_index(tmp_path, names_instance, capsys):
    """Test print_error_line when providing an explicit error_index override."""
    text = "DEVICES G1;"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    # 'DEVICES ' is 8 characters long. index 8 points to 'G'
    scanner.get_symbol()  # Scan 'DEVICES'
    scanner.print_error_line(error_index=8)
    
    captured = capsys.readouterr()
    output_lines = captured.out.split('\n')
    assert "DEVICES G1;" in output_lines[1]
    assert "        ^" in output_lines[2]

def test_scanner_print_error_index_error_handling(tmp_path, names_instance, capsys):
    """Test that print_error_line gracefully catches an IndexError if current_line goes out of bounds."""
    text = "DEVICES;"
    scanner = write_and_scan(tmp_path, text, names_instance)
    
    # Artificially corrupt the line state to force an IndexError
    scanner.current_line = 9999  
    
    scanner.print_error_line()
    captured = capsys.readouterr()
    assert "Could not render visual caret due to indexing error" in captured.out

def test_scanner_reserved_keyword_ids_is_set(tmp_path, names_instance):
    """Test that reserved_keyword_ids is optimized into a set collection during initialization."""
    scanner = write_and_scan(tmp_path, "DEVICES", names_instance)
    
    assert isinstance(scanner.reserved_keyword_ids, set)
    devices_id = names_instance.query("DEVICES")
    assert devices_id in scanner.reserved_keyword_ids