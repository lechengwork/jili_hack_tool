package main

import (
	"fmt"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/gin-gonic/gin"
)

func getEnv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func main() {
	port := getEnv("PORT", "8443")
	tlsMode := getEnv("TLS", "1") != "0"
	projectDir := getEnv("PROJECT_DIR", "..")
	absProject, _ := filepath.Abs(projectDir)
	gamesDir := getEnv("GAMES_DIR", filepath.Join(absProject, "games"))
	scheme := "https"
	if !tlsMode {
		scheme = "http"
	}
	serverURL := getEnv("SERVER_URL", scheme+"://localhost:"+port)

	root := loadRootConfig(filepath.Join(absProject, "config.json"))
	catalog := loadCatalog(absProject)
	games := scanGames(gamesDir, catalogNames(catalog))

	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("  JILI Mock Server")
	fmt.Println("═══════════════════════════════════════════")
	fmt.Printf("  Project : %s\n", absProject)
	fmt.Printf("  Games   : %s\n", gamesDir)
	fmt.Printf("  URL     : %s\n", serverURL)
	if tlsMode {
		fmt.Printf("  TLS     : 開啟（自簽憑證，瀏覽器需按「繼續前往」）\n")
	} else {
		fmt.Printf("  TLS     : 關閉（遊戲 JS 寫死 https://，可能連不上）\n")
	}
	fmt.Println("───────────────────────────────────────────")
	if len(games) == 0 {
		fmt.Println("  （尚無已擷取的遊戲）")
	}
	for _, g := range games {
		_, label := g.Mode()
		fmt.Printf("  [%s] %s — %s\n", g.GameID, orDefault(g.GameName, "?"), label)
	}
	fmt.Println("───────────────────────────────────────────")
	fmt.Printf("  面版: %s\n", serverURL)
	fmt.Println("═══════════════════════════════════════════")

	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	// CORS — 遊戲 JS 會跨來源打 API
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "*")
		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	})

	// 面版
	r.GET("/", servePanel(games, serverURL, absProject, gamesDir, root.Site))

	// 擷取 API
	r.POST("/api/capture/:gameid", handleStartCapture(absProject, gamesDir))
	r.GET("/api/capture/:gameid/status", handleCaptureStatus())

	// 共用資源（面版的遊戲圖示走這條）
	sharedDir := filepath.Join(gamesDir, "shared")
	r.GET("/shared/*path", func(c *gin.Context) {
		fp := filepath.Join(sharedDir, filepath.FromSlash(strings.TrimPrefix(c.Param("path"), "/")))
		if _, err := os.Stat(fp); err != nil {
			c.Status(http.StatusNotFound)
			return
		}
		c.File(fp)
	})

	// 每款遊戲的路由
	//
	// gin 的 catch-all "/*path" 不能和同一層的具體路徑並存，
	// 所以 GET 一律走單一 catch-all，在 handler 內部再分派：
	//   /webservice/event/*  → 204 遙測 stub
	//   WS 路徑              → WS replay
	//   錄到的 API path      → HTTP replay
	//   其餘                 → 靜態檔
	for _, g := range games {
		game := g
		grp := "/" + game.GameID

		var wsHandler gin.HandlerFunc
		var httpHandler gin.HandlerFunc
		replayPaths := map[string]bool{}

		if game.Config != nil {
			switch game.Config.Protocol.Transport {
			case "ws":
				wsHandler = handleWSReplay(game.Config, game.GameID)
			case "http":
				httpHandler = handleHTTPReplay(game.Config, newCursor())
				for p := range game.Config.HTTP.Replay {
					if !strings.HasPrefix(p, "/webservice/event/") {
						replayPaths[p] = true
					}
				}
			}
		}

		dispatch := func(c *gin.Context) {
			sub := c.Param("path")

			// 遙測：遊戲 JS 寫死會打，回 204 讓它安靜
			if strings.HasPrefix(sub, "/webservice/event/") {
				c.Status(http.StatusNoContent)
				return
			}
			// WebSocket 升級
			if wsHandler != nil && isWSUpgrade(c) {
				wsHandler(c)
				return
			}
			// 錄到的 API
			if httpHandler != nil && replayPaths[sub] {
				httpHandler(c)
				return
			}
			serveStaticFile(c, game, sub, serverURL)
		}

		r.GET(grp+"/*path", dispatch)
		r.HEAD(grp+"/*path", dispatch)

		// POST 沒有 catch-all 衝突問題，直接掛
		r.POST(grp+"/*path", func(c *gin.Context) {
			sub := c.Param("path")
			if strings.HasPrefix(sub, "/webservice/event/") {
				c.Status(http.StatusNoContent)
				return
			}
			if httpHandler != nil {
				httpHandler(c)
				return
			}
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error": "尚未擷取到 " + game.GameID + " 的後端流量",
				"path":  sub,
			})
		})
	}

	// 遊戲 JS 常用絕對路徑（/astarte2/... /smallicon/...），靠 Referer 推回所屬遊戲
	r.NoRoute(func(c *gin.Context) {
		urlPath := c.Request.URL.Path
		if ref := c.Request.Referer(); ref != "" {
			if u, err := url.Parse(ref); err == nil {
				seg := strings.SplitN(strings.TrimPrefix(u.Path, "/"), "/", 2)
				if len(seg) > 0 && seg[0] != "" {
					for _, g := range games {
						if g.GameID == seg[0] {
							serveStaticFile(c, g, urlPath, serverURL)
							return
						}
					}
				}
			}
		}
		// 最後退到 shared
		fp := filepath.Join(sharedDir, filepath.FromSlash(strings.TrimPrefix(urlPath, "/")))
		if _, err := os.Stat(fp); err == nil {
			c.File(fp)
			return
		}
		c.Status(http.StatusNotFound)
	})

	if tlsMode {
		certDir := filepath.Join(absProject, "jili_server")
		certPath, keyPath, err := ensureCert(certDir)
		if err != nil {
			fmt.Fprintln(os.Stderr, "TLS 憑證產生失敗:", err)
			os.Exit(1)
		}
		if err := r.RunTLS(":"+port, certPath, keyPath); err != nil {
			fmt.Fprintln(os.Stderr, "server error:", err)
			os.Exit(1)
		}
		return
	}
	if err := r.Run(":" + port); err != nil {
		fmt.Fprintln(os.Stderr, "server error:", err)
		os.Exit(1)
	}
}
