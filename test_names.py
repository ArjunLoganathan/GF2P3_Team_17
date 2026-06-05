"""Test the names module."""
import pytest
from names import Names

@pytest.fixture
def new_names():
    """Return a new instance of the Names class for each test."""
    return Names()

def test_initialization_reserved_keywords(new_names):
    """Test that reserved keywords are correctly populated upon initialization."""
    assert len(new_names.name_id_strings) == 17
    assert len(new_names.reserved_keyword_ids) == 17
    
    assert new_names.query("IMPORT") == 0
    assert new_names.query("SWITCH") == 6
    assert new_names.query("OUTPUT_PORTS") == 16

def test_unique_error_codes(new_names):
    """Test if unique_error_codes returns correct ranges and updates the count."""
    codes_1 = new_names.unique_error_codes(3)
    assert list(codes_1) == [0, 1, 2]
    assert new_names.error_code_count == 3

    codes_2 = new_names.unique_error_codes(2)
    assert list(codes_2) == [3, 4]
    assert new_names.error_code_count == 5


def test_lookup_empty_list(new_names):
    """Test that lookup gracefully handles an empty list."""
    ids = new_names.lookup([])
    assert ids == []
    assert len(new_names.name_id_strings) == 17

def test_unique_error_codes_type_error(new_names):
    """Test if unique_error_codes raises a TypeError for non-integer inputs."""
    with pytest.raises(TypeError):
        new_names.unique_error_codes(3.5)
        
    with pytest.raises(TypeError):
        new_names.unique_error_codes("two")


def test_lookup_adds_new_names(new_names):
    """Test if lookup correctly adds new names and assigns sequential IDs."""
    names_to_add = ["MY_GATE", "SIG_A", "TEMP_VAR"]
    
    ids = new_names.lookup(names_to_add)
    assert ids == [17, 18, 19]
    
    assert len(new_names.name_id_strings) == 20
    assert new_names.name_id_mapping["MY_GATE"] == 17


def test_lookup_handles_duplicates(new_names):
    """Test if lookup returns the same ID for existing names without duplicating."""
    # Use custom names, as the first 17 IDs (0-16) are taken by reserved keywords
    new_names.lookup(["GATE_A", "GATE_B"])
    
    ids = new_names.lookup(["GATE_A", "GATE_C", "GATE_B"])
    
    assert ids == [17, 19, 18]
    assert len(new_names.name_id_strings) == 20


def test_query(new_names):
    """Test if query returns the correct ID or None."""
    new_names.lookup(["CUSTOM_NAND", "CUSTOM_NOR"])
    
    assert new_names.query("CUSTOM_NAND") == 17
    assert new_names.query("CUSTOM_NOR") == 18
    
    assert new_names.query("NOT_EXIST") is None


def test_get_name_string(new_names):
    """Test if get_name_string returns the correct string or None for invalid IDs."""
    new_names.lookup(["NEW_DTYPE", "NEW_XOR"])
    
    # ID 0 is actually "IMPORT" from the reserved keywords!
    assert new_names.get_name_string(0) == "IMPORT"
    
    assert new_names.get_name_string(17) == "NEW_DTYPE"
    assert new_names.get_name_string(18) == "NEW_XOR"
    
    assert new_names.get_name_string(99) is None
    assert new_names.get_name_string(-1) is None

def test_query_invalid_types(new_names):
    """Test that querying non-string types safely returns None."""
    assert new_names.query(123) is None
    assert new_names.query(3.14) is None
    assert new_names.query(["NAND"]) is None

def test_get_string_alias(new_names):
    """Test that get_string perfectly mirrors get_name_string."""
    assert new_names.get_string(0) == "IMPORT"
    
    assert new_names.get_string(999) is None

def test_unique_error_codes_zero(new_names):
    """Test requesting zero error codes returns an empty sequence."""
    codes = new_names.unique_error_codes(0)
    assert list(codes) == []
    assert new_names.error_code_count == 0