"""461 input schema from this game's verified live requests, not another game.

f1/f2/f4 in context and f1/f2 in purchase remain neutral: no enum guessed.
Explicit zeros, unknown fields and original wire order stay in _wire.
"""
import math_adapter as a

def field(number,name,kind):return {'number':number,'name':name,'type':kind,'repeated':False}
a.SCHEMA.update({
    'Purchase461':[field(1,'f1','int32'),field(2,'f2','int32'),field(3,'amount','double')],
    'Context461':[field(1,'f1','int32'),field(2,'f2','int32'),field(4,'f4','int32')],
    'SpinRequest461':[field(1,'bet','double'),field(23,'purchase','Purchase461'),field(25,'context','Context461')]})

def request_to_math(payload):
    obj=a.decode_message(bytes(payload),'SpinRequest461')
    # Keep optional purchase absent for normal requests, instead of manufacturing it.
    if 23 not in a.fields(bytes(payload)):obj.pop('purchase',None)
    if math_to_request(obj)!=bytes(payload):raise ValueError('Complete 461 request byte roundtrip failed')
    return obj

def math_to_request(obj):return a.encode_message(obj,'SpinRequest461')
