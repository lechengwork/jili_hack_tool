#!/usr/bin/env python3
"""Initialize this new history-only login's WS session; never send bets/cashouts."""
import asyncio,json,time
from pathlib import Path
import websockets
import capture_history as h

async def run():
    entries=[json.loads(l) for l in (h.OUT/'index.local.jsonl').read_text().splitlines()]
    entry=next(e for e in entries if e['path']=='/sso-login.api'and e['status']==200)
    sso=json.loads((h.OUT/entry['file']).read_bytes());token=sso['token']
    async with websockets.connect('wss://uat-fish.jlfafafa1.com/aviator/ws/'+token,origin='https://uat-wbgame.jlfafafa3.com',open_timeout=20) as ws:
        first=await asyncio.wait_for(ws.recv(),15)
        with (h.SESSION/'history_ws_init.local.jsonl').open('a') as f:f.write(json.dumps({'dir':'RECV','ts':int(time.time()*1000),'hex':first.hex()})+'\n')
        print('Fresh history-only WebSocket initialized; no bet commands sent',flush=True)
        for frame in ['085f','0864','086912020802','086f12070a057a682d434e']:
            await ws.send(bytes.fromhex(frame))
        stop=asyncio.Event()
        async def heartbeat():
            while not stop.is_set():
                await ws.send(bytes.fromhex('0832'))
                try:await asyncio.wait_for(stop.wait(),2)
                except asyncio.TimeoutError:pass
        task=asyncio.create_task(heartbeat())
        try:
            result=await asyncio.to_thread(h.fetch,'POST','/v2/token',body={'Token':token})
            if result.get('Code')==0:
                (h.OUT/'token_response.local.json').write_text(json.dumps(result['Data'],ensure_ascii=False)+'\n')
                print('History token Data keys',list(result['Data'])if isinstance(result['Data'],dict)else type(result['Data']).__name__)
        finally:
            stop.set();await task
if __name__=='__main__':asyncio.run(run())
