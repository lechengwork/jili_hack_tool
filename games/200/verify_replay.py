#!/usr/bin/env python3
"""Offline replay tests: WebSocket protocol, local wallet, cyclic results and math edits."""
import argparse,base64,hashlib,importlib.util,json,os,socket,struct,tempfile,threading,time,unittest,urllib.request,sys
from copy import deepcopy
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent))
from routex.texture_variants import audit,webp_dimensions
ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['math','wire'],default='math');args=ap.parse_args()
os.environ['REPLAY_SOURCE']=args.source
import replay_server as server
from replay_pool import ReplayPool,codec

class ReplayTests(unittest.TestCase):
    def test_windows_webp_variants_and_http(self):
        report=audit(HERE/'static')
        self.assertTrue(report['passed'],[r for r in report['assets'] if r['status']!='ok'])
        self.assertGreaterEqual(report['required_webp'],22)
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        threading.Thread(target=httpd.serve_forever,daemon=True).start()
        try:
            for row in report['assets']:
                with urllib.request.urlopen('http://127.0.0.1:%d/%s'%(httpd.server_port,row['path'])) as response:
                    self.assertEqual(response.status,200)
                    self.assertEqual(response.headers.get_content_type(),'image/webp')
                    data=response.read()
                    self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
                    self.assertEqual(list(webp_dimensions(data)),list(row['dimensions']))
        finally:
            httpd.shutdown();httpd.server_close()

    def test_webp_preflight_rejects_missing_and_fake_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);astc=root/'example.astc'
            original=next((HERE/'static').rglob('*.astc')).read_bytes()
            astc.write_bytes(original)
            self.assertFalse(audit(root)['passed'])
            astc.with_suffix('.webp').write_bytes(original)
            self.assertFalse(audit(root)['passed'])
            astc.with_suffix('.webp').write_bytes(b'<html>error</html>')
            self.assertFalse(audit(root)['passed'])

    def client(self):
        sent=[];c=server.RoomSession(sent.append);c.join(4);c.phase='betting';c.deadline=time.monotonic()+100
        return c,sent

    def test_cycle_all_six_twice_and_local_wallet(self):
        pool=ReplayPool(args.source);balance=10000000;ids=[]
        for i in range(12):
            row,obj=pool.read(i);bets=[0]*12;bets[obj['winner']-1]=123
            balance-=123;wire,r=pool.settle(i,bets,balance);balance=r['balance_after'];ids.append(r['source_round'])
            self.assertEqual(r['total_win'],123*obj['return_odds'][obj['winner']-1])
            self.assertEqual(codec.wire_to_math(wire,'RECV')['data']['postCoin'],balance)
        self.assertEqual(ids[:6],ids[6:]);self.assertEqual(len(set(ids)),6)

    def test_welcome_is_synthetic_and_preserves_framework_configuration(self):
        sent=[];c=server.RoomSession(sent.append);c.welcome()
        frame=codec.decode_message(sent[0],'Command');d=codec.decode_message(codec.byte_array(frame['data']),'LoginDataAck')
        self.assertEqual(d['player']['uid'],200001);self.assertEqual(d['player']['name'],'Replay200')
        self.assertEqual(d['player']['wallet']['coin'],server.INITIAL_BALANCE)
        fields=codec.fields(codec.byte_array(frame['data']));self.assertIn(7,fields);self.assertIn(8,fields)
        self.assertNotIn(b'tryplayer',sent[0]);self.assertNotIn('bearer',json.dumps(server.local_sso()))

    def test_add_undo_double_clear_and_duplicate_ack(self):
        c,sent=self.client();start=c.balance
        def req(n,detail):return server.pack(22,'SpinReq',{'clientCheckNum':n,'detail':detail})
        a=req(0,[{'type':2,'bet':100000}]);c.wager(a);self.assertEqual(c.balance,start-100000)
        c.wager(a);self.assertEqual(c.balance,start-100000)
        c.wager(req(1,[{'type':2,'bet':100000},{'type':8,'bet':100000}]))
        self.assertEqual(c.bets[1],200000);self.assertEqual(c.bets[7],100000)
        c.wager(req(2,[{'type':2,'bet':-100000}]))
        self.assertEqual(c.bets[1],100000)
        c.wager(req(3,[{'type':2,'bet':-100000},{'type':8,'bet':-100000}]))
        self.assertEqual(c.balance,start);self.assertEqual(c.bets,[0]*12)
        before=c.balance
        with self.assertRaises(ValueError):c.wager(req(4,[{'type':2,'bet':-1}]))
        with self.assertRaises(ValueError):c.wager(req(4,[{'type':13,'bet':100}]))
        with self.assertRaises(ValueError):c.wager(req(4,[{'type':2,'bet':4000001}]))
        self.assertEqual(c.balance,before)
        ack=codec.wire_to_math(sent[-1],'RECV');self.assertEqual(ack['data']['accountID'],'200001')

    def test_locking_repeated_settlement_and_empty_round(self):
        c,sent=self.client();start=c.balance
        r=c.settle();self.assertEqual(r['total_win'],0);self.assertEqual(c.balance,start)
        with self.assertRaises(ValueError):c.settle()
        with self.assertRaises(ValueError):c.wager(server.pack(22,'SpinReq',{'detail':[{'type':2,'bet':100}]}))
        old=c.round_id;c.next_round();self.assertGreater(c.round_id,old)
        self.assertEqual(codec.wire_to_math(sent[-1],'RECV')['command'],17)
        c.deadline=time.monotonic()-1
        with self.assertRaises(ValueError):c.wager(server.pack(22,'SpinReq',{'detail':[{'type':2,'bet':100}]}))

    def test_math_reloads_and_invalid_edits_do_not_silently_fallback(self):
        rows=server.SAMPLES['rounds'];rid=rows[0]['round_id']
        with tempfile.TemporaryDirectory(prefix='pappu-replay-hotload-')as tmp:
            root=Path(tmp)
            for row in rows:(root/(row['round_id']+'.json')).write_text(json.dumps(row['original_math']))
            pool=ReplayPool('math',root);bets=[0]*12;bets[1]=100
            _,first=pool.settle(0,bets,1000000)
            p=root/(rid+'.json');changed=json.loads(p.read_text());changed.update(winner=2,pic=2)
            changed['return_odds'][1]=30;changed=codec.recalculate_round(changed);p.write_text(json.dumps(changed))
            wire,second=pool.settle(0,bets,1000000)
            self.assertNotEqual(first['winner'],second['winner']);self.assertEqual(second['total_win'],3000)
            self.assertEqual(codec.wire_to_math(wire,'RECV')['data']['bonus'][2],30)
            p.write_text('{bad JSON')
            with self.assertRaises(ValueError):pool.settle(0,bets,1000000)
            original=server.POOL
            try:
                server.POOL=pool;c,_=self.client();before=c.balance
                with self.assertRaises(ValueError):c.settle()
                self.assertEqual(c.balance,before);self.assertEqual(c.phase,'math-error')
            finally:server.POOL=original

    def test_real_http_websocket_room_protocol(self):
        old_bet,old_result=server.BET_SECONDS,server.RESULT_SECONDS
        server.BET_SECONDS=.6;server.RESULT_SECONDS=.1
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);httpd.daemon_threads=True
        threading.Thread(target=httpd.serve_forever,daemon=True).start();port=httpd.server_port
        sock=None
        try:
            with urllib.request.urlopen('http://127.0.0.1:%d/sso-login.api'%port)as response:
                sso=json.load(response);self.assertEqual(sso['profile']['account'],'local-replay-200')
            sock=socket.create_connection(('127.0.0.1',port),timeout=3);stream=sock.makefile('rb',buffering=0)
            key=base64.b64encode(b'0123456789abcdef').decode()
            sock.sendall(('GET /pappu/ws/local-replay-200 HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: '+key+'\r\n\r\n').encode())
            head=bytearray()
            while not head.endswith(b'\r\n\r\n'):head.extend(stream.read(1))
            self.assertIn(b'101',head)
            def recv():
                a,b=server.exact_read(stream,2);n=b&127
                if n==126:n=int.from_bytes(server.exact_read(stream,2),'big')
                elif n==127:n=int.from_bytes(server.exact_read(stream,8),'big')
                return server.exact_read(stream,n)
            def send(body):
                n=len(body);mask=b'1234';head=bytes([130,128|n])if n<126 else bytes([130,128|126])+struct.pack('>H',n)
                sock.sendall(head+mask+bytes(x^mask[i%4]for i,x in enumerate(body)))
            self.assertEqual(codec.decode_message(recv(),'Command')['type'],0)
            send(server.pack(10,'JoinThemeReq',{'themeId':1}));self.assertEqual(codec.wire_to_math(recv(),'RECV')['command'],10)
            send(server.pack(11,'JoinRoomReq',{'roomId':4}));self.assertEqual(codec.wire_to_math(recv(),'RECV')['command'],11)
            send(server.pack(26));sync=codec.wire_to_math(recv(),'RECV');self.assertEqual(sync['command'],24)
            send(server.pack(22,'SpinReq',{'clientCheckNum':0,'detail':[{'type':2,'bet':100000}]}))
            self.assertEqual(codec.wire_to_math(recv(),'RECV')['command'],22)
            result=codec.wire_to_math(recv(),'RECV');self.assertEqual(result['command'],18)
            self.assertEqual(result['data']['postCoin'],server.INITIAL_BALANCE-100000+result['data']['win'])
            self.assertEqual(codec.wire_to_math(recv(),'RECV')['command'],13)
            start=codec.wire_to_math(recv(),'RECV');self.assertEqual(start['command'],17)
            self.assertGreater(int(start['data']['wagers']),int(sync['data']['wagers']))
        finally:
            if sock:sock.close()
            httpd.shutdown();httpd.server_close();server.BET_SECONDS,server.RESULT_SECONDS=old_bet,old_result

    def test_script_declared_native_assets_are_present_and_hash_verified(self):
        report=json.loads((HERE/'replay_asset_sources.json').read_text())
        self.assertEqual(len(report['assets']),247)
        for row in report['assets']:
            asset=HERE/'static'/row['path'].lstrip('/')
            self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(),row['sha256'])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReplayTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'source':args.source,'passed':result.wasSuccessful(),'tests':result.testsRun,
            'cases':['six samples twice/cycle','synthetic identity/framework init','add/undo/clear/duplicate','locking/empty rounds',
                     'per-settlement hot reload/invalid JSON rejection','real HTTP+masked WebSocket init/join/sync/bet/end/next round',
                     '247 native existence assets/hash','all declared WebP variants/local HTTP 200/MIME/hash/dimensions',
                     'missing/ASTC-renamed-as-WebP/HTML rejection'],
            'browser_visual_validation':'separate; not implied by backend tests','network':'loopback only; no upstream fallback'}
    (HERE/('replay_validation_'+args.source+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful()else 1)
