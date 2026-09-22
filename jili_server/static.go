package main

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/gin-gonic/gin"
)

// LoadedGame 代表 games/<gameid>/ 底下一款已擷取的遊戲
type LoadedGame struct {
	GameID     string
	GameName   string
	StaticRoot string      // games/<gameid>/static
	SharedRoot string      // games/shared
	Config     *GameConfig // nil = 只有靜態資源，尚未擷取到協定
}

// Mode 回傳這款遊戲目前可用到什麼程度：(css class, 顯示文字)
func (g *LoadedGame) Mode() (string, string) {
	if g.Config == nil {
		return "static", "僅靜態"
	}
	switch g.Config.Protocol.Transport {
	case "http":
		n := 0
		for _, v := range g.Config.HTTP.Replay {
			n += len(v)
		}
		return "replay", "HTTP replay · " + itoa(n)
	case "ws":
		n := 0
		for _, c := range g.Config.WebSocket.Replay {
			n += len(c.Frames)
		}
		return "replay", "WS replay · " + itoa(n) + "f"
	}
	return "unknown", "協定未知"
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	var b []byte
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	return string(b)
}

// scanGames 掃描 games/ 目錄，載入每一款有 static/ 的遊戲
func scanGames(gamesDir string, names map[string]string) []*LoadedGame {
	entries, err := os.ReadDir(gamesDir)
	if err != nil {
		return nil
	}
	sharedRoot := filepath.Join(gamesDir, "shared")

	var games []*LoadedGame
	for _, e := range entries {
		if !e.IsDir() || e.Name() == "shared" {
			continue
		}
		id := e.Name()
		staticRoot := filepath.Join(gamesDir, id, "static")
		if _, err := os.Stat(staticRoot); err != nil {
			continue
		}
		g := &LoadedGame{
			GameID:     id,
			GameName:   names[id],
			StaticRoot: staticRoot,
			SharedRoot: sharedRoot,
		}
		if cfg, err := loadGameConfig(filepath.Join(gamesDir, id, "game_config.json")); err == nil {
			g.Config = cfg
		}
		games = append(games, g)
	}
	return games
}

// gameEntryURL 回傳遊戲主頁 URL（帶好指向本機的 query params）
func gameEntryURL(g *LoadedGame, serverURL string, site SiteConfig) string {
	gamePath := site.GamePath
	if gamePath == "" {
		gamePath = "/fg5/"
	}
	base := serverURL + "/" + g.GameID + gamePath

	// JILI 從 query param 讀後端域名，且存的是「反轉字串」。
	// 指向本機即可，不必像 habanero 那樣改寫 index.html。
	host := strings.TrimPrefix(strings.TrimPrefix(serverURL, "http://"), "https://")
	local := host + "/" + g.GameID
	q := "?ssoKey=local-mock-token" +
		"&lang=" + orDefault(site.Lang, "zh-CN") +
		"&apiId=" + orDefault(site.APIID, "1778") +
		"&be=" + reverse(local) +
		"&domain_platform=" + reverse(local) +
		"&gameID=" + g.GameID +
		"&gs=" + reverse(local) +
		"&iu=true&legalLang=true&skin=" + orDefault(site.Skin, "0")
	return base + q
}

func reverse(s string) string {
	r := []rune(s)
	for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {
		r[i], r[j] = r[j], r[i]
	}
	return string(r)
}

func orDefault(v, d string) string {
	if v == "" {
		return d
	}
	return v
}

// ─── 靜態檔服務 ──────────────────────────────────────────────────────────────

// serveStaticFile 從遊戲 static/ 找檔案，找不到再退到 games/shared/
func serveStaticFile(c *gin.Context, g *LoadedGame, subPath string, serverURL string) {
	if subPath == "" || subPath == "/" {
		c.Redirect(http.StatusFound, serverURL+"/"+g.GameID+"/fg5/")
		c.Abort()
		return
	}

	clean := filepath.FromSlash(strings.TrimPrefix(subPath, "/"))
	filePath := filepath.Join(g.StaticRoot, clean)

	info, err := os.Stat(filePath)
	if err != nil && g.SharedRoot != "" {
		// fallback：astarte2 / smallicon 這類跨遊戲共用資源
		sharedPath := filepath.Join(g.SharedRoot, clean)
		if si, se := os.Stat(sharedPath); se == nil {
			filePath, info, err = sharedPath, si, nil
		}
	}
	if err != nil {
		c.Status(http.StatusNotFound)
		c.Abort()
		return
	}

	if info.IsDir() {
		idx := filepath.Join(filePath, "index.html")
		if _, e2 := os.Stat(idx); e2 == nil {
			filePath = idx
		} else {
			c.Status(http.StatusNotFound)
			c.Abort()
			return
		}
	}

	c.File(filePath)
	c.Abort()
}

func serveGameStatic(g *LoadedGame, serverURL string) gin.HandlerFunc {
	return func(c *gin.Context) {
		serveStaticFile(c, g, c.Param("path"), serverURL)
	}
}
