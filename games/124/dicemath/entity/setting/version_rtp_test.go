package setting

import "testing"

// TestGetVersionRtp 測試版本字串 → RTP 的白名單對應。
//   - 每個合法版本(0800 … 0980、1020、1100、2000)回傳正確的 RTP 且 ok = true。
//   - 不在白名單的字串(例如 "unknown")回傳 ok = false。
func TestGetVersionRtp(t *testing.T) {
	tests := []struct {
		version string
		wantRtp float64
		wantOk  bool
	}{
		{"0800", 0, false}, // 不合法
		{"0880", 0.88, true},
		{"0920", 0.92, true},
		{"0940", 0.94, true},
		{"0950", 0.95, true},
		{"0960", 0.96, true},
		{"0970", 0.97, true},
		{"0975", 0.975, true},
		{"0980", 0.98, true},
		{"1020", 1.02, true},
		{"1100", 1.10, true},
		{"2000", 2.00, true},
		{"unknown", 0, false},
	}
	for _, tt := range tests {
		gotRtp, gotOk := GetVersionRtp(tt.version)
		if gotOk != tt.wantOk {
			t.Fatalf("GetVersionRtp(%q) ok = %v, want %v", tt.version, gotOk, tt.wantOk)
		}
		if gotOk && gotRtp != tt.wantRtp {
			t.Errorf("GetVersionRtp(%q) rtp = %v, want %v", tt.version, gotRtp, tt.wantRtp)
		}
	}
}

// TestAllowedVersions_AllResolveToValidRtp 測試 AllowedVersions 列出的每個版本都能在白名單查到 RTP。
//   - 防止「清單有列、switch 卻漏寫」造成某版本查不到。
func TestAllowedVersions_AllResolveToValidRtp(t *testing.T) {
	versions := AllowedVersions()
	if len(versions) == 0 {
		t.Fatal("AllowedVersions() returned an empty list")
	}
	for _, v := range versions {
		if _, ok := GetVersionRtp(v); !ok {
			t.Errorf("AllowedVersions() contains %q, but GetVersionRtp(%q) is not ok", v, v)
		}
	}
}
