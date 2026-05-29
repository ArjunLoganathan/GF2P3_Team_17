"""Test the names module."""
import pytest
from names import Names


@pytest.fixture
def new_names():
    """Return a new instance of the Names class for each test."""
    return Names()


def test_unique_error_codes(new_names):
    """Test if unique_error_codes returns correct ranges and updates the count."""
    codes_1 = new_names.unique_error_codes(3)
    assert list(codes_1) == [0, 1, 2]
    assert new_names.error_code_count == 3

    codes_2 = new_names.unique_error_codes(2)
    assert list(codes_2) == [3, 4]
    assert new_names.error_code_count == 5


def test_unique_error_codes_type_error(new_names):
    """Test if unique_error_codes raises a TypeError for non-integer inputs."""
    with pytest.raises(TypeError):
        new_names.unique_error_codes(3.5)
        
    with pytest.raises(TypeError):
        new_names.unique_error_codes("two")


def test_lookup_adds_new_names(new_names):
    """Test if lookup correctly adds new names and assigns sequential IDs."""
    names_to_add = ["SWITCH", "CLOCK", "AND"]
    
    ids = new_names.lookup(names_to_add)
    assert ids == [0, 1, 2]
    
    assert len(new_names.name_id_strings) == 3
    assert new_names.name_id_mapping["SWITCH"] == 0
    assert new_names.name_id_mapping["AND"] == 2


def test_lookup_handles_duplicates(new_names):
    """Test if lookup returns the same ID for existing names without duplicating."""
    # Add initial names
    new_names.lookup(["SWITCH", "CLOCK"])
    
    ids = new_names.lookup(["SWITCH", "OR", "CLOCK"])
    
    assert ids == [0, 2, 1]
    
    assert len(new_names.name_id_strings) == 3


def test_query(new_names):
    """Test if query returns the correct ID or None."""
    new_names.lookup(["NAND", "NOR"])
    
    assert new_names.query("NAND") == 0
    assert new_names.query("NOR") == 1
    
    assert new_names.query("XOR") is None


def test_get_name_string(new_names):
    """Test if get_name_string returns the correct string or None for invalid IDs."""
    new_names.lookup(["DTYPE", "XOR"])
    
    assert new_names.get_name_string(0) == "DTYPE"
    assert new_names.get_name_string(1) == "XOR"
    
    assert new_names.get_name_string(2) is None
    assert new_names.get_name_string(-1) is None