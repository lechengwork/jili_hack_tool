# watch_games.ps1 — 遊戲上架狀態儀表板(自己開著看)。Windows 版。
# 對應 watch_games.sh。用 config.json 的帳號週期性探每款遊戲能不能拿到 game_url。
#   ✓ 上架 = game_url=ok   ✗ 下架 = success+null   ! 抽風 = HTTP 500   ? 帳號不存在 = code 101
# 目標(★)一旦從 ✗ 翻成 ✓ 會響鈴 + 大字提示。
#   .\watch_games.ps1          持續盯(每 INTERVAL 秒,預設 180)
#   .\watch_games.ps1 --once   只跑一輪
#   $env:INTERVAL=120; .\watch_games.ps1

param([string]$Mode = "")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"; $env:LOGIN_RETRIES = "1"

$INTERVAL = if ($env:INTERVAL) { [int]$env:INTERVAL } else { 180 }
$ONCE = ($Mode -eq "--once")

# 你的兩組(標籤 / 帳號 / player_id / 要盯的遊戲,★=重點盯)
$STAR = [char]0x2605
$WATCH = @(
  @{ Label="USD代理"; Account="usd"; Player="streamerusd011";   Games="696$STAR 697" }
  @{ Label="THB代理"; Account="thb"; Player="testplayer001thb"; Games="540 696$STAR" }
)

function Probe {
  param([string]$Game,[string]$Account,[string]$Player)
  $out = (& python jili_login.py $Game --account $Account --player-id $Player 2>&1 | Out-String)
  if     ($out -match 'game_url=ok')   { return "OK" }
  elseif ($out -match 'code=101')      { return "NOACC" }
  elseif ($out -match 'HTTP 500')      { return "HTTP500" }
  elseif ($out -match 'game_url=null') { return "NULL" }
  else { $m=[regex]::Match($out,'HTTP \d+'); return ("?" + $(if ($m.Success){$m.Value}else{""})) }
}

$prev = @{}   # key "acct/player/gm" → 上一輪狀態
$n = 0
while ($true) {
  $n++; $ts = Get-Date -Format "MM-dd HH:mm:ss"
  Write-Host ""
  Write-Host ("第 {0} 輪  {1}  (每 {2}s;Ctrl+C 結束)" -f $n,$ts,$INTERVAL) -ForegroundColor White
  Write-Host ("  {0,-9} {1,-18} {2,-6} {3}" -f "代理","帳號","遊戲","狀態")
  Write-Host "  ────────────────────────────────────────────────────"
  foreach ($grp in $WATCH) {
    foreach ($tok in ($grp.Games -split '\s+' | Where-Object { $_ })) {
      $star = ""; $gm = $tok
      if ($gm.EndsWith([char]0x2605)) { $star = [char]0x2605; $gm = $gm.TrimEnd([char]0x2605) }
      $st = Probe -Game $gm -Account $grp.Account -Player $grp.Player
      switch ($st) {
        "OK"      { $col="Green";    $txt="✓ 上架(拿到 url)" }
        "NULL"    { $col="Red";      $txt="✗ 下架/停用(success+null)" }
        "HTTP500" { $col="Yellow";   $txt="! 500 抽風(暫時)" }
        "NOACC"   { $col="DarkGray"; $txt="? 帳號在該代理不存在" }
        default   { $col="DarkGray"; $txt="? $st" }
      }
      Write-Host ("  {0,-9} {1,-18} {2,-4}{3} " -f $grp.Label,$grp.Player,$gm,$star) -NoNewline
      Write-Host $txt -ForegroundColor $col
      $key = "$($grp.Account)/$($grp.Player)/$gm"
      if ($star -and $st -eq "OK" -and $prev.ContainsKey($key) -and $prev[$key] -ne "OK") {
        try { [console]::Beep(1000,400) } catch {}
        Write-Host ("  ★★★ {0} 上架了!可以跑  .\webcapture.ps1 {0}  了 ★★★" -f $gm) -ForegroundColor Green
      }
      $prev[$key] = $st
    }
  }
  if ($ONCE) { break }
  Start-Sleep -Seconds $INTERVAL
}
