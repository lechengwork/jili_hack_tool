package main

import (
	"encoding/json"
	"os"
)

// ─── game_config.json 結構 ────────────────────────────────────────────────────

type Protocol struct {
	Transport  string `json:"transport"`   // "http" | "ws" | "unknown"
	SpinTarget string `json:"spin_target"` // endpoint path 或 ws url
	WSBinary   bool   `json:"ws_binary"`
}

type HTTPReplayEntry struct {
	Status      int    `json:"status"`
	ContentType string `json:"content_type"`
	Body        string `json:"body"`
	BodyB64     string `json:"body_b64"`
	RequestBody string `json:"request_body"`
}

type HTTPEndpoint struct {
	Path    string         `json:"path"`
	Count   int            `json:"count"`
	Methods map[string]int `json:"methods"`
	Actions map[string]int `json:"actions"`
}

type HTTPSection struct {
	Endpoints []HTTPEndpoint               `json:"endpoints"`
	Replay    map[string][]HTTPReplayEntry `json:"replay"`
}

type WSFrame struct {
	Dir    string `json:"dir"` // SEND | RECV
	Binary bool   `json:"binary"`
	Hex    string `json:"hex"`
	Text   string `json:"text"`
}

type WSConnection struct {
	URL           string         `json:"url"`
	Frames        int            `json:"frames"`
	Sent          int            `json:"sent"`
	Recv          int            `json:"recv"`
	Binary        bool           `json:"binary"`
	BinaryFormats map[string]int `json:"binary_formats"`
}

type WSReplay struct {
	URL    string    `json:"url"`
	Frames []WSFrame `json:"frames"`
}

type WSSection struct {
	Connections []WSConnection `json:"connections"`
	Replay      []WSReplay     `json:"replay"`
}

type GameConfig struct {
	GameID     string      `json:"gameid"`
	GameURL    string      `json:"game_url"`
	CapturedAt string      `json:"captured_at"`
	Protocol   Protocol    `json:"protocol"`
	HTTP       HTTPSection `json:"http"`
	WebSocket  WSSection   `json:"websocket"`
}

func loadGameConfig(path string) (*GameConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg GameConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}

// ─── config.json（站台設定）────────────────────────────────────────────────

type SiteConfig struct {
	GameHost     string `json:"game_host"`
	GSHost       string `json:"gs_host"`
	PlatformHost string `json:"platform_host"`
	BEHost       string `json:"be_host"`
	GamePath     string `json:"game_path"`
	APIID        string `json:"api_id"`
	Lang         string `json:"lang"`
	Skin         string `json:"skin"`
}

type RootConfig struct {
	Site SiteConfig `json:"site"`
}

func loadRootConfig(path string) *RootConfig {
	cfg := &RootConfig{Site: SiteConfig{GamePath: "/fg5/", Lang: "zh-CN", Skin: "0"}}
	data, err := os.ReadFile(path)
	if err != nil {
		return cfg
	}
	_ = json.Unmarshal(data, cfg)
	if cfg.Site.GamePath == "" {
		cfg.Site.GamePath = "/fg5/"
	}
	return cfg
}
