package setting

// GetVersionRtp 取得版本字串對應的 RTP。
// version 不合法時 ok 回傳 false，rtp 為 0。
// 比照 lib/survivalroad/entity/setting/version_rtp.go 的 switch-case 白名單慣例：
// 這個 switch 本身就是「合法版本清單」的唯一真相來源。
// 注意：白名單合法不代表每個機台都支援(例如 4102 不支援 0800)，機台支援清單見各機台 setting。
func GetVersionRtp(version string) (rtp float64, ok bool) {
	switch version {
	case "0880":
		return 0.88, true
	case "0920":
		return 0.92, true
	case "0940":
		return 0.94, true
	case "0950":
		return 0.95, true
	case "0960":
		return 0.96, true
	case "0970":
		return 0.97, true
	case "0975":
		return 0.975, true
	case "0980":
		return 0.98, true
	case "1020":
		return 1.02, true
	case "1100":
		return 1.10, true
	case "2000":
		return 2.00, true
	}
	return 0, false
}

// AllowedVersions 取得白名單內所有版本字串
func AllowedVersions() []string {
	return []string{"0880", "0920", "0940", "0950", "0960", "0970", "0975", "0980", "1020", "1100", "2000"}
}
