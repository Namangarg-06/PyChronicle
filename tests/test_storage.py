import pytest
import time
from pychronicle.storage import StateStorage, serialize_value, deserialize_value

def test_serialization():
    # Test basic types
    assert serialize_value(123) == '123'
    assert serialize_value("hello") == '"hello"'
    assert serialize_value(True) == 'true'
    assert serialize_value(None) == 'null'

    # Test collections
    assert serialize_value([1, "2", True]) == '[1, "2", true]'
    assert serialize_value({"a": 1, "b": "hello"}) == '{"a": 1, "b": "hello"}'

    # Test custom object fallback
    class Dummy:
        def __repr__(self):
            return "<DummyObj>"
    
    assert serialize_value(Dummy()) == '"<DummyObj>"'

def test_deserialization():
    assert deserialize_value('123') == 123
    assert deserialize_value('"hello"') == "hello"
    assert deserialize_value('true') == True
    assert deserialize_value('null') is None
    assert deserialize_value('[1, "2", true]') == [1, "2", True]
    assert deserialize_value('{"a": 1, "b": "hello"}') == {"a": 1, "b": "hello"}

def test_state_storage_lifecycle():
    # Initialize in-memory database
    storage = StateStorage(":memory:")
    
    # Log some dummy variable mutations
    now = time.time_ns() // 1_000_000
    id1 = storage.log_state(5, "x", 10, timestamp_ms=now)
    id2 = storage.log_state(6, "y", "hello", timestamp_ms=now + 10)
    id3 = storage.log_state(7, "x", 20, timestamp_ms=now + 20)

    assert id1 is not None
    assert id2 is not None
    assert id3 is not None

    # Get history
    history = storage.get_history()
    assert len(history) == 3
    
    # Check chronological ordering
    assert history[0]["variable_name"] == "x"
    assert history[0]["value"] == 10
    assert history[0]["line_number"] == 5

    assert history[1]["variable_name"] == "y"
    assert history[1]["value"] == "hello"

    assert history[2]["variable_name"] == "x"
    assert history[2]["value"] == 20

    # Get latest variables at point in time
    vars_at_line = storage.get_variables_at_line(7)
    assert vars_at_line["x"] == 20
    assert vars_at_line["y"] == "hello"

    # Clear trace
    storage.clear()
    assert len(storage.get_history()) == 0

    storage.close()
