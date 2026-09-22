#!/usr/bin/env python3
"""
gen_server.py — Step 3: 檢查資料 + 編譯 server

用法: .venv/bin/python gen_server.py [GAMEID] [--run]

  GAMEID  可選。給了就檢查那款遊戲的資料是否完整。
  --run   編譯完直接啟動 server。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
GAMES_DIR = BASE / "games"
SERVER_DIR = BASE / "jili_server"


def check_game(gameid: str) -> bool:
    d = GAMES_DIR / gameid
    ok = True
    if not (d / "static").exists():
        print(f"  ✗ games/{gameid}/static/ 不存在")
        ok = False
    else:
        n = sum(1 for _ in (d / "static").rglob("*") if _.is_file())
        print(f"  ✓ static/  {n} 個檔案")

    cfg_path = d / "game_config.json"
    if not cfg_path.exists():
        print(f"  ⚠ game_config.json 不存在 → server 只會提供靜態資源")
        return ok

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    proto = cfg.get("protocol", {})
    transport = proto.get("transport", "unknown")
    print(f"  ✓ game_config.json  protocol={transport}")
    if transport == "unknown":
        print(f"  ⚠ 協定未判定，遊戲無法連線。重新擷取並確認有錄到後端流量。")
    elif transport == "http":
        n = sum(len(v) for v in cfg.get("http", {}).get("replay", {}).values())
        print(f"    HTTP replay: {n} 筆回應")
    elif transport == "ws":
        n = sum(len(c.get("frames", [])) for c in cfg.get("websocket", {}).get("replay", []))
        print(f"    WS replay: {n} frames")
    return ok


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("gameid", nargs="?")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--port", default="8443")
    args = ap.parse_args()

    print("═" * 60)
    print("  JILI — Build Server")
    print("═" * 60)

    if args.gameid:
        print(f"\n[檢查] gameID {args.gameid}")
        check_game(args.gameid)
    else:
        found = [d.name for d in GAMES_DIR.iterdir()
                 if d.is_dir() and d.name != "shared" and (d / "static").exists()]
        print(f"\n[檢查] 已擷取 {len(found)} 款: {', '.join(sorted(found)) or '（無）'}")
        for gid in sorted(found):
            print(f"\n  · gameID {gid}")
            check_game(gid)

    print(f"\n[編譯] go build ...")
    r = subprocess.run(["go", "build", "-o", "jili_server", "."], cwd=SERVER_DIR)
    if r.returncode != 0:
        sys.exit("[錯誤] 編譯失敗")
    print("[編譯] ✓ jili_server/jili_server")

    print("\n" + "═" * 60)
    print("  啟動指令：")
    print(f"    cd {SERVER_DIR}")
    print(f"    ./jili_server")
    print(f"  面版： https://localhost:{args.port}   （自簽憑證，首次要按「繼續前往」）")
    print("═" * 60)

    if args.run:
        import os
        env = dict(os.environ, PORT=args.port)
        os.execve(str(SERVER_DIR / "jili_server"), [str(SERVER_DIR / "jili_server")], env)


if __name__ == "__main__":
    main()
