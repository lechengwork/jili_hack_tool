package main

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

// ─── HTTP Replay ─────────────────────────────────────────────────────────────

// replayCursor 記錄每個 path 播到第幾筆，循環播放
type replayCursor struct {
	mu  sync.Mutex
	idx map[string]int
}

func newCursor() *replayCursor { return &replayCursor{idx: map[string]int{}} }

func (rc *replayCursor) next(path string, n int) int {
	if n == 0 {
		return -1
	}
	rc.mu.Lock()
	defer rc.mu.Unlock()
	i := rc.idx[path]
	rc.idx[path] = (i + 1) % n
	return i
}

// handleHTTPReplay 依照擷取到的順序循環回放該 path 的回應
func handleHTTPReplay(cfg *GameConfig, cursor *replayCursor) gin.HandlerFunc {
	return func(c *gin.Context) {
		path := c.Param("path")
		if path == "" {
			path = c.Request.URL.Path
		}
		if !strings.HasPrefix(path, "/") {
			path = "/" + path
		}

		entries, ok := cfg.HTTP.Replay[path]
		if !ok {
			// 試著只比對最後一段（有些 path 會帶動態前綴）
			for k, v := range cfg.HTTP.Replay {
				if strings.HasSuffix(k, path) || strings.HasSuffix(path, k) {
					entries, ok = v, true
					break
				}
			}
		}
		if !ok || len(entries) == 0 {
			c.JSON(http.StatusNotFound, gin.H{
				"error": "no recorded response for " + path,
				"hint":  "重新擷取一次讓這個 endpoint 被錄到",
			})
			return
		}

		e := entries[maxInt(cursor.next(path, len(entries)), 0)]
		ct := e.ContentType
		if ct == "" {
			ct = "application/json"
		}
		status := e.Status
		if status == 0 {
			status = http.StatusOK
		}

		if e.BodyB64 != "" {
			raw, err := base64.StdEncoding.DecodeString(e.BodyB64)
			if err == nil {
				c.Data(status, ct, raw)
				return
			}
		}
		c.Data(status, ct, []byte(e.Body))
	}
}

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// ─── WebSocket Replay ────────────────────────────────────────────────────────

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  8192,
	WriteBufferSize: 8192,
}

// handleWSReplay 客戶端連上後，照擷取順序回放伺服器端 frame。
// 規則：每收到一個 client frame，就把「下一批 RECV frame」推回去，
// 直到遇到下一個 SEND 為止。播完從頭循環。
func handleWSReplay(cfg *GameConfig, gameID string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if len(cfg.WebSocket.Replay) == 0 {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error": "no recorded websocket traffic for game " + gameID,
			})
			return
		}
		// 用 frame 最多的那條連線
		best := cfg.WebSocket.Replay[0]
		for _, r := range cfg.WebSocket.Replay {
			if len(r.Frames) > len(best.Frames) {
				best = r
			}
		}

		conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			fmt.Printf("[WS] upgrade 失敗: %v\n", err)
			return
		}
		defer conn.Close()
		fmt.Printf("[WS] %s 連線，回放 %d frames\n", gameID, len(best.Frames))

		pos := 0
		// 先推出開頭的 RECV（handshake / init 之類，client 尚未送任何東西）
		pos = pushRecv(conn, best.Frames, pos)

		for {
			if _, _, err := conn.ReadMessage(); err != nil {
				fmt.Printf("[WS] %s 斷線: %v\n", gameID, err)
				return
			}
			// 跳過腳本裡的 SEND（那是錄製時 client 送的）
			for pos < len(best.Frames) && best.Frames[pos].Dir == "SEND" {
				pos++
			}
			if pos >= len(best.Frames) {
				pos = 0 // 循環
			}
			pos = pushRecv(conn, best.Frames, pos)
		}
	}
}

// pushRecv 推出從 pos 起連續的 RECV frame，回傳新的 pos
func pushRecv(conn *websocket.Conn, frames []WSFrame, pos int) int {
	for pos < len(frames) && frames[pos].Dir == "RECV" {
		f := frames[pos]
		var err error
		if f.Binary {
			raw, derr := hexDecode(f.Hex)
			if derr == nil {
				err = conn.WriteMessage(websocket.BinaryMessage, raw)
			}
		} else {
			err = conn.WriteMessage(websocket.TextMessage, []byte(f.Text))
		}
		if err != nil {
			return pos
		}
		pos++
		time.Sleep(15 * time.Millisecond) // 避免一次灌爆 client
	}
	return pos
}

func hexDecode(s string) ([]byte, error) {
	if len(s)%2 != 0 {
		return nil, fmt.Errorf("odd hex length")
	}
	out := make([]byte, len(s)/2)
	for i := 0; i < len(out); i++ {
		var hi, lo byte
		var err error
		if hi, err = hexVal(s[i*2]); err != nil {
			return nil, err
		}
		if lo, err = hexVal(s[i*2+1]); err != nil {
			return nil, err
		}
		out[i] = hi<<4 | lo
	}
	return out, nil
}

func hexVal(c byte) (byte, error) {
	switch {
	case c >= '0' && c <= '9':
		return c - '0', nil
	case c >= 'a' && c <= 'f':
		return c - 'a' + 10, nil
	case c >= 'A' && c <= 'F':
		return c - 'A' + 10, nil
	}
	return 0, fmt.Errorf("bad hex char %q", c)
}

// isWSUpgrade 判斷這個請求是不是 WebSocket 升級
func isWSUpgrade(c *gin.Context) bool {
	return strings.EqualFold(c.GetHeader("Upgrade"), "websocket") &&
		strings.Contains(strings.ToLower(c.GetHeader("Connection")), "upgrade")
}
