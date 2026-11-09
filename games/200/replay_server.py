#!/usr/bin/env python3
"""Pappu local-only HTTP/WebSocket replay. No live URLs, credentials or upstream fallback."""
import base64,hashlib,json,math,mimetypes,os,re,struct,threading,time,sys
from copy import deepcopy
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit
from replay_pool import ReplayPool,codec

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
from asset_archives import materialize as _materialize_archives
_materialize_archives(HERE/'static')
PORT=int(os.environ.get('REPLAY_PORT','8201'))
INITIAL_BALANCE=codec.wire_money(int(os.environ.get('REPLAY_BALANCE','3000000')))
BET_SECONDS=float(os.environ.get('REPLAY_BET_SECONDS','7.6'))
RESULT_SECONDS=float(os.environ.get('REPLAY_RESULT_SECONDS','16'))
if not 0<BET_SECONDS<=60 or not 0<RESULT_SECONDS<=120:raise ValueError('Invalid replay timing')
POOL=ReplayPool(os.environ.get('REPLAY_SOURCE','math'),os.environ.get('MATH_DIR'),
                [v for v in os.environ.get('SELECT_ROUNDS','').split(',')if v])
SAMPLES=POOL.samples
UID=SAMPLES['uid']
TRANSPORT=(HERE/'replay_transport.js').read_bytes()+b'\n;'+(HERE/'replay_ui.js').read_bytes()
STATUS={'network':'local-only; no upstream fallback','wallet':'simulated','source':POOL.source,
        'connections':0,'rounds_finished':0,'bets_accepted':0,'bets_rejected':0,'missing':[],
        'frontend_errors':[],'recent_rounds':[],'clients':{},'pool_count':len(POOL.rows),'ui_events':[]}
STATUS_LOCK=threading.RLock()

def pack(command,name=None,data=None):
    body=codec.encode_message(data or {},name)if name else b''
    return codec.encode_message({'type':command,'data':list(body)},'Command')

def exact_read(stream,size):
    out=bytearray()
    while len(out)<size:
        part=stream.read(size-len(out))
        if not part:raise EOFError
        out.extend(part)
    return bytes(out)

def ws_recv(stream):
    b1,b2=exact_read(stream,2);opcode=b1&15
    if b1&112 or not b1&128:raise ValueError('Unsupported fragmented/compressed WebSocket frame')
    n=b2&127
    if n==126:n=int.from_bytes(exact_read(stream,2),'big')
    elif n==127:n=int.from_bytes(exact_read(stream,8),'big')
    if n>1024*1024:raise ValueError('Oversized local WebSocket frame')
    if not b2&128:raise ValueError('Client frames must be masked')
    mask=exact_read(stream,4);data=exact_read(stream,n)
    return opcode,bytes(v^mask[i%4]for i,v in enumerate(data))

def ws_send(stream,payload,opcode=2):
    n=len(payload)
    head=bytes([128|opcode,n])if n<126 else bytes([128|opcode,126])+struct.pack('>H',n)if n<65536 else bytes([128|opcode,127])+struct.pack('>Q',n)
    stream.write(head+payload);stream.flush()

def local_sso():
    return {'homeUrl':'','linecode':0,'token':'local-replay-200','response':{'error':0,'message':'OK','time':int(time.time())},
            'platformVersion':'local-replay','lobbyMode':0,'disableFullScreen':0,'country':'Indonesia','certId':0,'certArea':0,
            'isnewplayer':0,'clientApiParam':{},'itaAuthId':'','thousandthMode':'','eventBannerId':0,'subDivision':'',
            'profile':{'id':str(UID),'aid':UID,'apiId':1778,'transactionMode':1,'subAgentCode':1,'isLobbyOpen':False,
            'meta':{'agentAccount':'local-replay-only'},'platform':'web','lobbyMode':0,'switchOffs':[26,27,44,70],
            'wallets':None,'nickname':'Replay200','newNickname':'Replay200','siteId':0,'account':'local-replay-200',
            'coin':INITIAL_BALANCE,'isJPEnabled':0,'linecode':0,'prefix':'replay','betLevel':-1,'betValue':0,'license':0,
            'isGiftCodeOpen':False,'freeSpinBetValue':0,'apiType':0,'walletType':2,'liveId':'','liveSourceUrls':{}}}

class RoomSession:
    def __init__(self,send,client_id='test'):
        self.send=send;self.client_id=str(client_id);self.lock=threading.RLock();self.stop=threading.Event()
        self.balance=INITIAL_BALANCE;self.room=None;self.phase='lobby';self.deadline=None;self.bets=[0]*12
        self.index=0;self.round_id=900000000000000000;self.generation=0;self.running=False;self.last_request=None
        self.history=deepcopy(SAMPLES['room']['history']);self.last_result=None

    def welcome(self):
        frame=codec.decode_message(bytes.fromhex(SAMPLES['welcome_hex']),'Command')
        d=codec.decode_message(codec.byte_array(frame['data']),'LoginDataAck')
        d['player']['wallet']['coin']=self.balance
        frame['data']=list(codec.encode_message(d,'LoginDataAck'))
        self.send(codec.encode_message(frame,'Command'))

    def update_status(self):
        with STATUS_LOCK:STATUS['clients'][self.client_id]={'phase':self.phase,'room':self.room,'wagers':str(self.round_id),
            'balance':self.balance,'bets':self.bets[:],'source_round':self.last_result.get('source_round')if self.last_result else None}

    def room_ack(self):
        d=deepcopy(SAMPLES['room']);d.update(roomId=self.room,status=1 if self.phase in('pending','betting')else 2,
            countDown=max(0,int(math.ceil((self.deadline-time.monotonic())if self.deadline else BET_SECONDS))),
            wagers=str(self.round_id),coin=self.balance,history=deepcopy(self.history))
        d['history']['roomID']=self.room
        d['table']={'area':[{'type':i,'player':1 if i and self.bets[i-1]else 0,'coin':self.bets[i-1]if i else 0}for i in range(13)]}
        return d

    def join(self,room):
        if not 0<=room<len(SAMPLES['theme']['rooms']):raise ValueError('Unknown replay room')
        with self.lock:
            if self.room==room and self.phase not in('lobby','closed'):
                self.send(pack(11,'JoinRoomAck',self.room_ack()));return
            if self.phase in('pending','betting'):self.balance+=sum(self.bets)
            self.generation+=1;self.running=False;self.room=room;self.phase='pending';self.bets=[0]*12
            self.deadline=None;self.round_id+=1;self.last_request=None
            self.send(pack(11,'JoinRoomAck',self.room_ack()));self.update_status()

    def sync(self):
        with self.lock:
            if self.room is None:return
            if self.phase=='pending':
                self.phase='betting';self.deadline=time.monotonic()+BET_SECONDS
            self.send(pack(24,'JoinRoomAck',self.room_ack()))
            if not self.running:
                self.running=True;threading.Thread(target=self.play,args=(self.generation,),daemon=True).start()
            self.update_status()

    def wager(self,raw):
        with self.lock:
            if self.phase!='betting' or self.deadline is None or time.monotonic()>=self.deadline:raise ValueError('Betting is closed')
            if raw==self.last_request:
                self.send(self.last_ack);return
            req=codec.decode_message(codec.byte_array(codec.decode_message(raw,'Command')['data']),'SpinReq')
            if req['cheat'] or req['vipEnd']:raise ValueError('Unsupported replay wager mode')
            if not req['detail']:raise ValueError('Empty wager')
            next_bets=self.bets[:]
            for b in req['detail']:
                t=b['type']
                if type(t)is not int or not 1<=t<=12:raise ValueError('Invalid bet area')
                delta=codec.money(b['bet'],signed=True)
                next_bets[t-1]=codec.money(next_bets[t-1]+delta)
                if next_bets[t-1]>4000000:raise ValueError('Local replay area limit 4,000,000 exceeded')
            cost=sum(next_bets)-sum(self.bets)
            if cost>self.balance:raise ValueError('Insufficient simulated balance')
            self.balance=codec.wire_money(self.balance-cost);self.bets=next_bets
            req['accountID']=str(UID)
            ack=pack(22,'SpinReq',req)
            self.last_request=raw;self.last_ack=ack;self.send(ack)
            with STATUS_LOCK:STATUS['bets_accepted']+=1
            self.update_status()

    def settle(self):
        with self.lock:
            if self.phase!='betting':raise ValueError('Round already settled')
            self.phase='locked';self.update_status()
            try:wire,record=POOL.settle(self.index,self.bets,self.balance)
            except Exception:
                self.phase='math-error';self.update_status();raise
            self.balance=record['balance_after'];record.update(served_round=str(self.round_id),room=self.room)
            self.phase='result';self.last_result=record;self.send(wire);self.index+=1
            self.history['list'].append({'reward':[record['winner']],'bonus':record['return_odds'][record['winner']-1]})
            self.history['list']=self.history['list'][-36:];self.history['roomID']=self.room
            self.send(pack(13,'RoomHistory',self.history))
            with STATUS_LOCK:
                STATUS['rounds_finished']+=1;STATUS['recent_rounds']=(STATUS['recent_rounds']+[record])[-20:]
            self.update_status();print('[200 replay result] '+json.dumps(record),flush=True)
            return record

    def next_round(self):
        with self.lock:
            if self.phase!='result':raise ValueError('Previous round did not settle')
            self.bets=[0]*12;self.last_request=None;self.round_id+=1;self.phase='betting';self.deadline=time.monotonic()+BET_SECONDS
            self.send(pack(17,'RoomStart',{'wagers':str(self.round_id)}));self.update_status()

    def play(self,generation):
        try:
            while not self.stop.is_set() and generation==self.generation:
                if self.stop.wait(max(0,self.deadline-time.monotonic())):break
                if generation!=self.generation:break
                self.settle()
                if self.stop.wait(RESULT_SECONDS):break
                if generation!=self.generation:break
                self.next_round()
        except (OSError,ConnectionError):self.stop.set()
        except Exception as error:
            with STATUS_LOCK:STATUS['frontend_errors'].append('math/replay: '+str(error))
            print('[200 replay paused] '+str(error),flush=True)

    def receive(self,raw):
        try:d=codec.decode_message(raw,'Command');command=d['type']
        except ValueError:
            # Shared-framework login request precedes game requests; welcome is already sent.
            if self.phase=='lobby':return
            raise
        if command==50:self.send(pack(50));return
        if command==0:return
        print('[200 replay request] cmd=%d'%command,flush=True)
        if command in(10,14):self.send(pack(10,'JoinThemeAck',SAMPLES['theme']));return
        if command==11:
            q=codec.decode_message(codec.byte_array(d['data']),'JoinRoomReq');self.join(q['roomId']);return
        if command==26:self.sync();return
        if command==22:
            try:self.wager(raw)
            except ValueError as error:
                with STATUS_LOCK:STATUS['bets_rejected']+=1
                print('[200 replay rejected] '+str(error),flush=True)
                self.send(pack(24,'JoinRoomAck',self.room_ack()))
            return
        if command==12:
            with self.lock:
                if self.phase in('pending','betting'):self.balance+=sum(self.bets)
                self.generation+=1;self.running=False;self.phase='lobby';self.room=None;self.bets=[0]*12
                self.send(pack(12));self.update_status()
            return
        response=112 if command==111 else command
        if str(response)in SAMPLES['auxiliary']:self.send(bytes.fromhex(SAMPLES['auxiliary'][str(response)]))

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args):pass
    def handle(self):
        try:super().handle()
        except (ConnectionResetError,BrokenPipeError):pass
    def send(self,code,data=b'',ctype='application/json'):
        if isinstance(data,str):data=data.encode()
        if ctype.startswith('text/')or'javascript'in ctype or'json'in ctype:ctype+='; charset=utf-8'
        self.send_response(code);self.send_header('Content-Length',str(len(data)));self.send_header('Content-Type',ctype)
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','*')
        self.send_header('Cache-Control','no-store');self.end_headers()
        try:
            if self.command!='HEAD':self.wfile.write(data)
        except OSError:pass
    def json(self,value):self.send(200,json.dumps(value,ensure_ascii=False))
    def do_OPTIONS(self):self.send(204)
    def api(self,path):
        if path.startswith('/__wasmpatch__/'):
            message=unquote(path[len('/__wasmpatch__/'):])
            with STATUS_LOCK:STATUS['ui_events']=(STATUS['ui_events']+[message])[-30:]
            print('[200 replay UI] '+message,flush=True);self.send(200,b'','image/gif');return True
        if path=='/ping':self.json({'time':int(time.time()*1000)});return True
        if re.search(r'/landingpage(?:/|$)',path):
            self.send(200,'<!doctype html><meta charset="utf-8"><p>Pappu 本地重播，活動服務停用。</p>','text/html');return True
        if 'sso-login'in path:self.json(local_sso());return True
        if path=='/__replay_status':
            with STATUS_LOCK:self.json(deepcopy(STATUS))
            return True
        if path=='/time/1/current':self.json({'time':int(time.time()*1000),'timestamp':int(time.time()*1000)});return True
        if path.startswith(('/webservice/','/subagentservice/','/rankingservice/','/vipservice/','/eventservice/','/favoriteservice/','/tournamentservice/','/promotionservice/','/smartnotice/')):
            self.send(200,b'','application/x-protobuf');return True
        return False
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>1024*1024:self.send(413);return
        body=self.rfile.read(n);path=urlsplit(self.path).path
        if path=='/__replay_diagnostic':
            d=json.loads(body)
            with STATUS_LOCK:STATUS['frontend_errors'].append(d)
            print('[200 frontend] '+json.dumps(d,ensure_ascii=False),flush=True);self.json({});return
        if not self.api(path):self.send(404,b'{}')
    def do_HEAD(self):self.do_GET()
    def do_GET(self):
        path=urlsplit(self.path).path
        if self.headers.get('Upgrade','').lower()=='websocket':return self.ws(path)
        if self.api(path):return
        rel=unquote(path).lstrip('/')or'pappu/index.html'
        # The original loader selects /aeond/ on localhost. Reuse the identical
        # captured framework versions locally; the dedicated Chrome uses /aeon/.
        if rel.startswith('aeond/'):rel='aeon/'+rel[len('aeond/'):]
        if rel.endswith('/'):rel+='index.html'
        root=HERE/'static';target=(root/rel).resolve()
        # Synthetic replay identities may select any avatar; use a cached local
        # portrait for missing cosmetic icons, never an upstream request.
        if re.fullmatch(r'smallicon/headIcons/\d+\.png',rel)and not target.exists():target=root/'smallicon/headIcons/46.png'
        if root not in target.parents or not target.is_file():
            with STATUS_LOCK:
                if path not in STATUS['missing']:STATUS['missing'].append(path);print('[200 replay missing] '+path,flush=True)
            self.send(404,b'not found','text/plain');return
        data=target.read_bytes()
        if target.name.startswith('system.bundle')and target.suffix=='.js':data=TRANSPORT+b'\n;'+data
        if target.suffix=='.html':
            data=re.sub(rb'<script[^>]*googletagmanager[^>]*>.*?</script>',b'',data,flags=re.S)
            badge='<div style="position:fixed;right:4px;top:0;z-index:2147483647;background:#243545;color:#fff;font:12px sans-serif;padding:4px;pointer-events:none">Pappu 本地重播 · 模擬餘額</div>'.encode()
            data=data.replace(b'</body>',badge+b'</body>')
        ctype={'.js':'application/javascript','.wasm':'application/wasm','.bin':'application/octet-stream','.astc':'application/octet-stream','.webp':'image/webp','.json':'application/json'}.get(target.suffix,mimetypes.guess_type(str(target))[0]or'application/octet-stream')
        self.send(200,data,ctype)
    def ws(self,path):
        if not path.startswith('/pappu/ws/'):
            self.send(404,b'unknown replay socket');return
        key=self.headers.get('Sec-WebSocket-Key','')
        if not key:self.send(400);return
        self.close_connection=True
        accept=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        self.send_response(101);self.send_header('Upgrade','websocket');self.send_header('Connection','Upgrade');self.send_header('Sec-WebSocket-Accept',accept);self.end_headers()
        send_lock=threading.RLock()
        def send(data,opcode=2):
            with send_lock:ws_send(self.wfile,data,opcode)
        with STATUS_LOCK:STATUS['connections']+=1;client_id=STATUS['connections']
        client=RoomSession(send,client_id)
        try:
            client.welcome();client.update_status()
            while not client.stop.is_set():
                op,payload=ws_recv(self.rfile)
                if op==8:send(b'',8);break
                if op==9:send(payload,10);continue
                if op==10:continue
                if op==2:client.receive(payload)
        except (OSError,EOFError,ConnectionError):pass
        except Exception as error:
            with STATUS_LOCK:STATUS['frontend_errors'].append('socket: '+str(error))
            print('[200 replay socket] '+str(error),flush=True)
        finally:client.stop.set();client.phase='closed';client.update_status()

if __name__=='__main__':
    sys.path.insert(0,str(HERE.parent.parent))
    from routex.texture_variants import audit
    textures=audit(HERE/'static')
    if not textures['passed']:
        raise SystemExit('WebP texture preflight failed (%d/%d valid). Run routex/texture_variants.py games/200/static --fetch --report games/200/texture_validation.json before replay.'%(textures['valid_webp'],textures['required_webp']))
    runtime=HERE/'replay';runtime.mkdir(exist_ok=True)
    (runtime/'server.pid').write_text(str(os.getpid())+'\n')
    ThreadingHTTPServer.daemon_threads=True
    print('[200 replay] http://127.0.0.1:%d; source=%s; samples=%d; offline only'%(PORT,POOL.source,len(POOL.rows)),flush=True)
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
