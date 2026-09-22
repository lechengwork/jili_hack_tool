# JILI 696 — Route X mock server

Serves the JILI front-end and impersonates the backend `/fg5/req` API with our own
keys. The crypto/transport layer is fully solved and **verified end-to-end against the
genuine `crypto.wasm`** (see "Verification" below). Spec: `../PROTOCOL_SOLVED.md`.

## Files
| file | role |
|---|---|
| `fg5.py` | crypto core: protobuf + X25519/AES-256-GCM/Ed25519. Parses requests, builds responses. |
| `gen_and_patch.py` | step ①: generate mock keypair (`mockkeys.json`) + patch `crypto.wasm`'s two baked pubs → ours (`crypto.patched.wasm`). |
| `server.py` | step ②③: HTTP(S) server — static files, `/sso-login.api`, `/fg5/req`, and serves the patched wasm. |
| `verify.py` | self-consistency test (plays both client & server sides in Python). |
| `mockkeys.json` | generated mock private/public keys (git-ignore this). |

## Run
```bash
../.venv/bin/python3 gen_and_patch.py      # once: keys + crypto.patched.wasm
../.venv/bin/python3 verify.py             # sanity: crypto core (6 checks)
../.venv/bin/python3 server.py             # serve (HTTPS :8443 by default)
# open the URL it prints; accept the self-signed cert.
```
Env: `PORT` `HOST` `TLS=0/1` `GAME_PATH` `CRYPTO_WASM` (path substring identifying the
crypto wasm, default `crypto`) `CERT`/`KEY` (supply your own cert instead of self-signed).

## How it works
1. **Patch** — `crypto.wasm` bakes two server pubs (XOR-0xAA obfuscated, 4×8-byte chunks
   each). `gen_and_patch.py` finds each chunk by content and overwrites it with our pub's
   chunk. The client then trusts OUR keys.
2. **Serve** — the reversed `gs`/`be` URL params point back at our host (WASM un-reverses
   them), so the client's `/sso-login.api` and `/fg5/req` calls hit us. `crypto.wasm` is
   fetched at runtime (not in the static mirror), so `server.py` intercepts any `*.wasm`
   whose path contains `CRYPTO_WASM` and returns the patched bytes. Unmatched paths are
   logged (`[404]`) — watch for the real wasm path on first run and set `CRYPTO_WASM`.
3. **Respond** — for each `/fg5/req`, read `f4=client_pub`, derive `key = X25519(mock_x_priv,
   client_pub)`, build the outer wrapper, encrypt (AES-256-GCM, empty AAD), and sign
   (`Ed25519_sign(mock_ed_priv, nonce‖ct)`). Reply `sig(64)‖nonce(12)‖ct‖tag`.
4. **Keepalive WS** — the client also opens `wss://<gs>/lifeservice/ws2`. `server.py`
   answers the upgrade (`Upgrade: websocket` GET), declines permessage-deflate, and speaks
   the captured keepalive protocol: on the client's first (binary protobuf) frame it sends
   the single text frame `{"error":0}`; the periodic `{"cmdType":-1,...}` heartbeats get
   no reply (matching the real server); pings get pongs. No crypto, no game logic — but
   **without it the client can't open the life channel and bails out with MSG 999.1**
   ("无法连接服务器"). Frame reference: `../games/696/traffic_raw.json` (`websockets[0]`, 38 frames).

### Response outer-wrapper field numbers (verified against real WASM)
`f3=type (varint)`, `f5=data (bytes)`, `f6=error_msg (string)`, `f7=ret (varint)`.
**Not** `f1..f4` — the older note was wrong; it only ever tested the all-zero `"0800"`
case where every field defaults, so a wrong field number silently emptied real payloads.
`data` (f5) carries the inner game protobuf (spin board etc., see `../games/696/SCHEMA.md`).

## Verification (proof it works)
`verify.py` proves the Python core is self-consistent. The **real-WASM** proof:
swap `crypto.patched.wasm` over `../games/696/crypto.wasm`, then feed a mock response to
`../harness_run2.js` with **no runtime patch** — the genuine WASM resolves:
- spin  → `{"type":0,"ret":0,"error_msg":"","data":[10,134,1,...]}` (183-byte payload)
- balance → `{"type":2,...,"data":[10,13,8,4,...]}`

i.e. file-patch + our keys + our crypto envelope all pass Ed25519 verify + X25519 + AES-GCM
decrypt + protobuf parse, delivering both `type` and `data`.

## Status (2026-08-31)
- **Crypto/transport `/fg5/req`:** solved + real-WASM verified (above).
- **Keepalive `/lifeservice/ws2`:** implemented — this was the visible cause of MSG 999.1
  in the last live test (the loader looped on a 404'd WS upgrade). Now answered; the
  `{"error":0}` handshake + heartbeat-drain is unit-tested against the captured frames.
- **Next likely blocker:** the handshake/config reply is still a fake minimal `{type:0}`
  (see below), so after the WS clears 999.1 the game may stall at init on an empty config.
  That's the data gap, not crypto — capture the config plaintext to close it.

## Known limitation (data gap, not crypto)
We only have **decrypted** samples for message types **0 (spin), 2 (balance), 58** —
`../games/696/responses.jsonl` (payload under key `raw`). The handshake/config response and
the periodic poll/ack plaintexts were never captured (they're encrypted with the real
server key in `fg5_exchanges.json`; we can't decrypt those). So:
- **Crypto/transport: complete and proven.** Any request gets a valid, correctly-mapped,
  signed+encrypted response.
- **Full game playability: blocked** on those missing plaintexts — the browser game likely
  stalls at init because it never receives a real config. `server.py` replies with a minimal
  valid `{type:0}` for unmapped request kinds and logs `[gap] request kind '<kind>' ...`.
  To close it: capture a heap dump containing the config/poll responses and add them to
  `responses.jsonl` + `KIND_TYPE` in `server.py`. No new crypto work is required.
