#!/usr/bin/env bash
# watch_games.sh — 遊戲上架狀態儀表板(自己開著看)。bash 3.2 相容。
# 用 config.json 的 login_accounts(--account)＋各組自己的 player_id,週期性探每款遊戲能不能拿到 game_url。
#   ✓ 上架   = game_url=ok          ✗ 下架   = success+null
#   ! 抽風   = HTTP 500(暫時性)      ? 帳號不存在 = code 101
# 目標(★)一旦從 ✗ 翻成 ✓ 會響鈴 + 大字提示。
#
# 用法:  ./watch_games.sh          持續盯(每 INTERVAL 秒)
#        ./watch_games.sh --once   只跑一輪
#        INTERVAL=120 ./watch_games.sh
set -u
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=.venv/bin/python
INTERVAL="${INTERVAL:-180}"
ONCE=""; [ "${1:-}" = "--once" ] && ONCE=1

# ── 你的兩組(標籤 | --account | player_id | 要盯的遊戲,空白分隔;★=重點盯) ──
WATCH=(
  "USD代理 | usd | streamerusd011   | 696★ 697"
  "THB代理 | thb | testplayer001thb | 540 696★"
)

if [ -t 1 ]; then
  g=$'\033[32m'; r=$'\033[31m'; y=$'\033[33m'; d=$'\033[90m'; b=$'\033[1m'; x=$'\033[0m'
else g=""; r=""; y=""; d=""; b=""; x=""; fi

STATEF="$(mktemp -t watchgames)"        # 記上一輪狀態:每行 "key<TAB>status"
trap 'rm -f "$STATEF"' EXIT

probe(){ # $1=game $2=account $3=player → OK/NULL/HTTP500/NOACC/?
  local out
  out=$(LOGIN_RETRIES=1 "$PY" jili_login.py "$1" --account "$2" --player-id "$3" 2>&1 \
        | grep -vE 'NotOpenSSLWarning|warnings.warn')
  if   printf '%s' "$out" | grep -q 'game_url=ok';   then echo OK
  elif printf '%s' "$out" | grep -q 'code=101';      then echo NOACC
  elif printf '%s' "$out" | grep -q 'HTTP 500';      then echo HTTP500
  elif printf '%s' "$out" | grep -q 'game_url=null'; then echo NULL
  else echo "\?$(printf '%s' "$out" | grep -oE 'HTTP [0-9]+' | head -1)"; fi
}

n=0
while :; do
  n=$((n+1)); ts=$(date '+%m-%d %H:%M:%S')
  printf '\n%s第 %d 輪  %s%s  (每 %ss;Ctrl+C 結束)\n' "$b" "$n" "$ts" "$x" "$INTERVAL"
  printf '  %-9s %-18s %-6s %s\n' "代理" "帳號" "遊戲" "狀態"
  printf '  ────────────────────────────────────────────────────\n'
  NEWSTATE="$(mktemp -t watchgames)"
  for grp in "${WATCH[@]}"; do
    label=$(printf '%s' "$grp" | cut -d'|' -f1 | xargs)
    acct=$( printf '%s' "$grp" | cut -d'|' -f2 | xargs)
    player=$(printf '%s' "$grp" | cut -d'|' -f3 | xargs)
    games=$(printf '%s' "$grp" | cut -d'|' -f4)
    for gm in $games; do
      star=""; case "$gm" in *★) star="★"; gm="${gm%★}";; esac
      st=$(probe "$gm" "$acct" "$player")
      case "$st" in
        OK)      col="$g"; txt="✓ 上架(拿到 url)";;
        NULL)    col="$r"; txt="✗ 下架/停用(success+null)";;
        HTTP500) col="$y"; txt="! 500 抽風(暫時)";;
        NOACC)   col="$d"; txt="? 帳號在該代理不存在";;
        *)       col="$d"; txt="? $st";;
      esac
      printf '  %-9s %-18s %-4s%s %s%s%s\n' "$label" "$player" "$gm" "$star" "$col" "$txt" "$x"
      key="$acct/$player/$gm"
      printf '%s\t%s\n' "$key" "$st" >> "$NEWSTATE"
      if [ -n "$star" ] && [ "$st" = OK ]; then
        prev=$(grep -F "$key	" "$STATEF" 2>/dev/null | tail -1 | cut -f2)
        if [ -n "$prev" ] && [ "$prev" != OK ]; then
          printf '\a%s%s  ★★★ %s 上架了!可以跑  ./webcapture.sh %s  了 ★★★%s\n' "$b" "$g" "$gm" "$gm" "$x"
        fi
      fi
    done
  done
  mv -f "$NEWSTATE" "$STATEF"
  [ -n "$ONCE" ] && break
  sleep "$INTERVAL"
done
