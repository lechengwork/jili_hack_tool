#!/usr/bin/env bash
# stop.sh — 停 JILI 124 回放 server + 關回放 Chrome
pkill -f 'ws_replay_server.py' 2>/dev/null && echo "server 已停" || echo "server 沒在跑"
pkill -f 'jili124-replay-profile' 2>/dev/null && echo "Chrome 已關" || echo "Chrome 沒在跑"
