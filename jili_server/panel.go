package main

import (
	"encoding/json"
	"fmt"
	"html"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// ─── 擷取工作管理 ────────────────────────────────────────────────────────────

type CaptureJob struct {
	GameID  string
	Status  string // running | done | error
	Log     []string
	Started time.Time
	mu      sync.Mutex
}

func (j *CaptureJob) append(line string) {
	j.mu.Lock()
	defer j.mu.Unlock()
	j.Log = append(j.Log, line)
	if len(j.Log) > 400 {
		j.Log = j.Log[len(j.Log)-400:]
	}
}

func (j *CaptureJob) snapshot() (string, []string) {
	j.mu.Lock()
	defer j.mu.Unlock()
	out := make([]string, len(j.Log))
	copy(out, j.Log)
	return j.Status, out
}

func (j *CaptureJob) setStatus(s string) {
	j.mu.Lock()
	j.Status = s
	j.mu.Unlock()
}

var (
	jobsMu sync.Mutex
	jobs   = map[string]*CaptureJob{}
)

// handleStartCapture 啟動 run_game.py（背景執行，輸出串到 job log）
func handleStartCapture(projectDir, gamesDir string) gin.HandlerFunc {
	return func(c *gin.Context) {
		gameID := strings.TrimSpace(c.Param("gameid"))
		if gameID == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "missing gameid"})
			return
		}

		var body struct {
			URL   string `json:"url"`
			Spins int    `json:"spins"`
		}
		_ = c.ShouldBindJSON(&body)

		jobsMu.Lock()
		if j, ok := jobs[gameID]; ok {
			j.mu.Lock()
			running := j.Status == "running"
			j.mu.Unlock()
			if running {
				jobsMu.Unlock()
				c.JSON(http.StatusOK, gin.H{"status": "running"})
				return
			}
		}
		job := &CaptureJob{GameID: gameID, Status: "running", Started: time.Now()}
		jobs[gameID] = job
		jobsMu.Unlock()

		py := filepath.Join(projectDir, ".venv", "bin", "python")
		if _, err := os.Stat(py); err != nil {
			py = "python3"
		}
		args := []string{filepath.Join(projectDir, "run_game.py"), gameID}
		if body.URL != "" {
			args = append(args, "--url", body.URL)
		}
		if body.Spins > 0 {
			args = append(args, "--spins", fmt.Sprint(body.Spins))
		}

		cmd := exec.Command(py, args...)
		cmd.Dir = projectDir
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			job.setStatus("error")
			job.append("stdout pipe: " + err.Error())
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		cmd.Stderr = cmd.Stdout
		if err := cmd.Start(); err != nil {
			job.setStatus("error")
			job.append("start: " + err.Error())
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		job.append(fmt.Sprintf("$ %s %s", py, strings.Join(args, " ")))

		go func() {
			buf := make([]byte, 4096)
			var carry string
			for {
				n, rerr := stdout.Read(buf)
				if n > 0 {
					carry += string(buf[:n])
					for {
						i := strings.IndexByte(carry, '\n')
						if i < 0 {
							break
						}
						job.append(strings.TrimRight(carry[:i], "\r"))
						carry = carry[i+1:]
					}
				}
				if rerr != nil {
					if carry != "" {
						job.append(carry)
					}
					break
				}
			}
			werr := cmd.Wait()
			cfgPath := filepath.Join(gamesDir, gameID, "game_config.json")
			if _, statErr := os.Stat(cfgPath); statErr == nil {
				job.setStatus("done")
				job.append("== 擷取完成，重新整理頁面套用 ==")
			} else if werr != nil {
				job.setStatus("error")
				job.append("== 失敗: " + werr.Error() + " ==")
			} else {
				job.setStatus("error")
				job.append("== 結束但沒有產出 game_config.json ==")
			}
		}()

		c.JSON(http.StatusOK, gin.H{"status": "started"})
	}
}

func handleCaptureStatus() gin.HandlerFunc {
	return func(c *gin.Context) {
		gameID := c.Param("gameid")
		jobsMu.Lock()
		job, ok := jobs[gameID]
		jobsMu.Unlock()
		if !ok {
			c.JSON(http.StatusOK, gin.H{"status": "idle", "log": []string{}})
			return
		}
		st, logLines := job.snapshot()
		c.JSON(http.StatusOK, gin.H{"status": st, "log": logLines})
	}
}

// ─── games.json ──────────────────────────────────────────────────────────────

type CatalogEntry struct {
	GameID   string `json:"gameid"`
	GameName string `json:"gamename"`
	Note     string `json:"note"`
}

func loadCatalog(projectDir string) []CatalogEntry {
	data, err := os.ReadFile(filepath.Join(projectDir, "games.json"))
	if err != nil {
		return nil
	}
	var out []CatalogEntry
	if json.Unmarshal(data, &out) != nil {
		return nil
	}
	return out
}

func catalogNames(entries []CatalogEntry) map[string]string {
	m := map[string]string{}
	for _, e := range entries {
		m[e.GameID] = e.GameName
	}
	return m
}

// ─── 面版 ────────────────────────────────────────────────────────────────────

func servePanel(games []*LoadedGame, serverURL, projectDir, gamesDir string, site SiteConfig) gin.HandlerFunc {
	return func(c *gin.Context) {
		catalog := loadCatalog(projectDir)
		loaded := map[string]*LoadedGame{}
		for _, g := range games {
			loaded[g.GameID] = g
		}

		// 目錄裡有、但 games.json 沒列到的，也要顯示
		seen := map[string]bool{}
		for _, e := range catalog {
			seen[e.GameID] = true
		}
		for _, g := range games {
			if !seen[g.GameID] {
				catalog = append(catalog, CatalogEntry{GameID: g.GameID, GameName: g.GameName})
			}
		}

		var ready, pending strings.Builder
		nReady := 0
		for _, e := range catalog {
			g := loaded[e.GameID]
			name := e.GameName
			if name == "" && g != nil {
				name = g.GameName
			}
			if name == "" {
				name = "game " + e.GameID
			}
			icon := iconHTML(gamesDir, e.GameID)

			if g != nil {
				nReady++
				cls, label := g.Mode()
				ready.WriteString(fmt.Sprintf(
					`<a class="card" href="%s" target="_blank">%s<div class="name">%s</div>`+
						`<div class="id">#%s</div><span class="badge %s">%s</span></a>`,
					html.EscapeString(gameEntryURL(g, serverURL, site)), icon,
					html.EscapeString(name), e.GameID, cls, html.EscapeString(label)))
			} else {
				pending.WriteString(fmt.Sprintf(
					`<div class="card dim" id="card-%s">%s<div class="name">%s</div>`+
						`<div class="id">#%s</div>`+
						`<button class="badge btn" onclick="cap('%s')">擷取</button></div>`,
					e.GameID, icon, html.EscapeString(name), e.GameID, e.GameID))
			}
		}

		page := panelHead(nReady, len(catalog)) +
			`<h2 class="sec">已擷取</h2><div class="grid">` + ready.String() + `</div>` +
			`<h2 class="sec">未擷取</h2><div class="grid">` + pending.String() + `</div>` +
			panelTail()

		c.Header("Content-Type", "text/html; charset=utf-8")
		c.String(http.StatusOK, page)
	}
}

func iconHTML(gamesDir, gameID string) string {
	for _, suffix := range []string{"_cn.jpg", "_en.jpg", "_cn.png", "_en.png"} {
		p := filepath.Join(gamesDir, "shared", "smallicon", "Icons", gameID+suffix)
		if _, err := os.Stat(p); err == nil {
			return fmt.Sprintf(`<div class="icon"><img src="/shared/smallicon/Icons/%s%s" alt=""></div>`,
				gameID, suffix)
		}
	}
	return `<div class="icon">🎰</div>`
}

func panelHead(ready, total int) string {
	return fmt.Sprintf(`<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JILI Mock Server</title><style>
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0d1117;color:#e6edf3;padding:32px 40px}
h1{color:#f0883e;margin:0 0 4px;font-size:1.6rem}
p.sub{color:#8b949e;margin:0 0 24px;font-size:.9rem}
h2.sec{font-size:.85rem;text-transform:uppercase;letter-spacing:.08em;color:#8b949e;margin:32px 0 12px;font-weight:600}
.bar{display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap}
.bar input{flex:1;min-width:320px;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:9px 12px;color:#e6edf3;font-size:.85rem;font-family:ui-monospace,SFMono-Regular,monospace}
.bar input:focus{outline:none;border-color:#f0883e}
.bar button{background:#f0883e;color:#0d1117;border:0;border-radius:8px;padding:9px 20px;font-weight:600;cursor:pointer;font-size:.85rem}
.bar button:hover{background:#ffa657}
.hint{color:#6e7681;font-size:.78rem;margin:0 0 20px}
.grid{display:flex;flex-wrap:wrap;gap:14px}
.card{display:block;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:14px;width:150px;text-decoration:none;color:#e6edf3;transition:border-color .15s,transform .15s}
.card:hover{border-color:#f0883e;transform:translateY(-2px)}
.card.dim{opacity:.5}
.icon{font-size:2rem;margin-bottom:8px;height:74px;display:flex;align-items:center;justify-content:center}
.icon img{width:100%%;height:74px;object-fit:cover;border-radius:8px;display:block}
.name{font-weight:600;font-size:.82rem;margin-bottom:2px;line-height:1.3;word-break:break-word}
.id{color:#6e7681;font-size:.72rem;margin-bottom:8px;font-family:ui-monospace,monospace}
.badge{display:block;text-align:center;font-size:.7rem;padding:4px 8px;border-radius:6px;font-weight:600;width:100%%}
.replay{background:#0f3d2e;color:#3fb950}
.static{background:#3d2e0f;color:#d29922}
.unknown{background:#30363d;color:#8b949e}
.btn{background:#1f6feb;color:#fff;border:0;cursor:pointer;font-family:inherit}
.btn:hover:not(:disabled){background:#388bfd}
.btn:disabled{opacity:.6;cursor:not-allowed}
@keyframes pulse{0%%,100%%{opacity:.5}50%%{opacity:.9}}
.capturing{animation:pulse 1.4s ease-in-out infinite;border-color:#1f6feb!important}
#logbox{position:fixed;right:0;bottom:0;width:min(560px,100vw);max-height:52vh;background:#010409;border:1px solid #30363d;border-radius:12px 0 0 0;display:none;flex-direction:column;box-shadow:0 -4px 24px rgba(0,0,0,.6)}
#logbox.on{display:flex}
#loghead{padding:8px 14px;border-bottom:1px solid #30363d;font-size:.78rem;color:#8b949e;display:flex;justify-content:space-between;align-items:center}
#loghead b{color:#f0883e}
#loghead span{cursor:pointer;padding:0 6px}
#log{overflow:auto;padding:10px 14px;font-family:ui-monospace,SFMono-Regular,monospace;font-size:.72rem;line-height:1.55;white-space:pre-wrap;color:#c9d1d9}
</style></head><body>
<h1>🎰 JILI Mock Server</h1>
<p class="sub">已擷取 %d / %d 款</p>
<div class="bar">
  <input id="url" placeholder="貼上含 ssoKey 的完整遊戲 URL（留空則用 config.json 的登入設定）">
  <button onclick="capFromUrl()">擷取</button>
</div>
<p class="hint">下方卡片按「擷取」即可逐款抓（走 config.json 的 LoginGame 自動換 URL）。上面的輸入框是備援：貼含 ssoKey 的完整 URL — 注意這種 URL <b>只能用一次</b>。開抓前先確認 Surfshark 已連到巴西。</p>
`, ready, total)
}

func panelTail() string {
	return `
<div id="logbox"><div id="loghead"><span>擷取中：<b id="logid"></b></span><span onclick="document.getElementById('logbox').classList.remove('on')">✕</span></div><div id="log"></div></div>
<script>
function showLog(id){document.getElementById('logid').textContent='#'+id;document.getElementById('logbox').classList.add('on');}
function capFromUrl(){
  var u=document.getElementById('url').value.trim();
  if(!u){alert('請貼上遊戲 URL，或直接按卡片上的「擷取」');return;}
  var m=u.match(/[?&]gameID=(\d+)/i);
  if(!m){alert('URL 裡找不到 gameID 參數');return;}
  start(m[1],u);
}
function cap(id){start(id,null);}
function start(id,url){
  var card=document.getElementById('card-'+id);
  if(card){card.classList.add('capturing');var b=card.querySelector('.btn');if(b){b.textContent='擷取中…';b.disabled=true;}}
  showLog(id);
  document.getElementById('log').textContent='啟動中…';
  fetch('/api/capture/'+id,{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url:url||''})})
    .then(function(r){return r.json();})
    .then(function(){poll(id);})
    .catch(function(e){document.getElementById('log').textContent='啟動失敗: '+e;});
}
function poll(id){
  fetch('/api/capture/'+id+'/status').then(function(r){return r.json();}).then(function(d){
    var el=document.getElementById('log');
    el.textContent=(d.log||[]).join('\n');
    el.scrollTop=el.scrollHeight;
    var card=document.getElementById('card-'+id);
    if(d.status==='running'){setTimeout(function(){poll(id);},1500);return;}
    if(card){
      card.classList.remove('capturing');
      var b=card.querySelector('.btn');
      if(b){
        if(d.status==='done'){b.textContent='✓ 重新整理';b.disabled=false;b.onclick=function(){location.reload();};}
        else{b.textContent='失敗，重試';b.disabled=false;b.onclick=function(){cap(id);};}
      }
    }
  });
}
</script></body></html>`
}
