"""573 request codec; names follow observed fields, not another game's enums."""
import math_adapter as a

def request_to_math(payload):
    obj = a.decode_message(bytes(payload), 'Bet')
    for number, name in [(23, 'purchase'), (25, 'context'), (26, 'f26')]:
        if number not in a.fields(bytes(payload)):
            obj.pop(name, None)
    if math_to_request(obj) != bytes(payload):
        raise ValueError('Complete 573 request byte round-trip failed')
    return obj

def math_to_request(obj):
    return a.encode_message(obj, 'Bet')
