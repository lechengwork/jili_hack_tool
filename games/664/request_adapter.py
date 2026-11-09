"""664 observed SPIN request shape. Unknown selector/context meanings stay neutral."""
import math_adapter as a

def f(n,name,t):return {'number':n,'name':name,'type':t,'repeated':False}
a.SCHEMA.update({
 'Purchase664':[f(1,'f1','int32'),f(2,'f2','int32'),f(3,'amount','double')],
 'Context664':[f(1,'f1','int32'),f(2,'f2','int32'),f(4,'f4','int32')],
 'Extra664':[f(1,'f1','int32')],
 'SpinRequest664':[f(1,'bet','double'),f(23,'purchase','Purchase664'),f(25,'context','Context664'),f(26,'extra','Extra664')]})
def request_to_math(payload):
 obj=a.decode_message(bytes(payload),'SpinRequest664')
 for n,k in [(23,'purchase'),(25,'context'),(26,'extra')]:
  if n not in a.fields(bytes(payload)):obj.pop(k,None)
 if math_to_request(obj)!=bytes(payload):raise ValueError('Complete 664 request byte roundtrip failed')
 return obj

def math_to_request(obj):return a.encode_message(obj,'SpinRequest664')
