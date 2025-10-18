"""
JCS (JSON Canonicalization Scheme) Implementation
RFC-8785 compatible canonicalization for policy signatures.

This module provides deterministic JSON serialization:
- Object keys sorted by Unicode code points
- Strings escaped (\\, ", control chars → \\uXXXX)
- Numbers normalized (no -0, minimal exponent notation)
- UTF-8 byte serialization
"""

import math
from typing import Any


def canonicalize(obj: Any) -> bytes:
    """
    Canonicalize a JSON-serializable object to bytes.

    Args:
        obj: JSON-serializable object (dict, list, str, int, float, bool, None)

    Returns:
        UTF-8 encoded canonical representation
    """
    return _serialize(obj).encode('utf-8')


def _serialize(obj: Any) -> str:
    """Recursively serialize object to canonical string."""
    if obj is None:
        return 'null'
    elif obj is True:
        return 'true'
    elif obj is False:
        return 'false'
    elif isinstance(obj, str):
        return _serialize_string(obj)
    elif isinstance(obj, (int, float)):
        return _serialize_number(obj)
    elif isinstance(obj, list):
        return _serialize_array(obj)
    elif isinstance(obj, dict):
        return _serialize_object(obj)
    else:
        raise TypeError(f"Unsupported type for canonicalization: {type(obj)}")


def _serialize_string(s: str) -> str:
    """Serialize string with proper escaping."""
    result = ['"']
    for char in s:
        code = ord(char)
        if char == '"':
            result.append('\\"')
        elif char == '\\':
            result.append('\\\\')
        elif char == '\b':
            result.append('\\b')
        elif char == '\f':
            result.append('\\f')
        elif char == '\n':
            result.append('\\n')
        elif char == '\r':
            result.append('\\r')
        elif char == '\t':
            result.append('\\t')
        elif code < 0x20:  # Control characters
            result.append(f'\\u{code:04x}')
        else:
            result.append(char)
    result.append('"')
    return ''.join(result)


def _serialize_number(n: float) -> str:
    """
    Serialize number in canonical form.
    - Convert -0 to 0
    - Use minimal representation (no unnecessary .0 or exponents)
    - Exponent notation: lowercase 'e', no '+', minimal digits
    """
    # Handle special cases
    if n == 0:
        return '0'
    if math.isnan(n) or math.isinf(n):
        raise ValueError(f"Cannot canonicalize NaN or Infinity: {n}")

    # Check if it's an integer
    if isinstance(n, int) or (isinstance(n, float) and n.is_integer()):
        return str(int(n))

    # For floats, use Python's default representation, then clean up
    s = repr(n)

    # Remove unnecessary trailing zeros after decimal point
    if '.' in s and 'e' not in s and 'E' not in s:
        s = s.rstrip('0').rstrip('.')

    # Normalize exponent notation
    if 'E' in s:
        s = s.replace('E', 'e')
    if 'e+' in s:
        s = s.replace('e+', 'e')

    return s


def _serialize_array(arr: list) -> str:
    """Serialize array."""
    if not arr:
        return '[]'
    elements = [_serialize(item) for item in arr]
    return '[' + ','.join(elements) + ']'


def _serialize_object(obj: dict) -> str:
    """Serialize object with sorted keys."""
    if not obj:
        return '{}'

    # Sort keys by Unicode code points (Python's default string sort)
    sorted_keys = sorted(obj.keys())

    pairs = []
    for key in sorted_keys:
        key_str = _serialize_string(key)
        value_str = _serialize(obj[key])
        pairs.append(f'{key_str}:{value_str}')

    return '{' + ','.join(pairs) + '}'


def test_canonicalize():
    """Self-test function."""
    # Test basic types
    assert canonicalize(None) == b'null'
    assert canonicalize(True) == b'true'
    assert canonicalize(False) == b'false'
    assert canonicalize(0) == b'0'
    assert canonicalize(42) == b'42'
    assert canonicalize("hello") == b'"hello"'

    # Test string escaping
    assert canonicalize("hello\nworld") == b'"hello\\nworld"'
    assert canonicalize('say "hi"') == b'"say \\"hi\\""'

    # Test arrays
    assert canonicalize([1, 2, 3]) == b'[1,2,3]'
    assert canonicalize([]) == b'[]'

    # Test objects with key sorting
    result = canonicalize({"z": 1, "a": 2, "m": 3})
    assert result == b'{"a":2,"m":3,"z":1}'

    # Test nested structures
    result = canonicalize({
        "numbers": [1, 2, 3],
        "string": "test",
        "nested": {"b": 2, "a": 1}
    })
    expected = b'{"nested":{"a":1,"b":2},"numbers":[1,2,3],"string":"test"}'
    assert result == expected

    print("✅ All JCS canonicalization tests passed")


if __name__ == '__main__':
    test_canonicalize()
