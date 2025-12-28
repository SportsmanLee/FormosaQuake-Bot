# Spec: CWA CSV 公告 Bot（最終規格）

以中央氣象署網站的 CSV 端點作為唯一資料源：啟動時先 `GET /zh-tw/earthquake/data/` 建立 session/cookies，再 `POST /zh-tw/earthquake/csv` 下載 **Big5、逗號分隔** CSV。每 **60s** 輪詢一次，因查詢只能選「月」，每輪抓「本月+上月」合併去重後取 **Top N=20**。所有事件（含 <4）都寫入 seen state；只有 **最大震度 ≥4** 才會發 Discord 公告，且只對「已發過且仍≥4」的事件做訊息 edit。輪詢 loop 已加入「可選」退避機制（連續失敗指數退避，上限可設定）。

## Steps

1. 建立資料源會話：固定 headers（UA/Origin/Referer），用 cookie jar；啟動/失效先 GET `data/`，再 POST `csv`。
2. 每 60s 輪詢兩個月份：各抓一次 CSV（本月、上月），Big5 解碼、逗號解析成列。
3. 合併去重與取樣：以 `event_key` 聚合、依 `地震時間` 新→舊排序，取 Top 20 進入後續處理。
4. 寫入 state（SQLite）：Top 20 全部更新 `seen_events`（包含 <4、解析失敗也要記錄 raw）。
5. 強度門檻與發送：解析 `最大震度` 為可比較值；若 `<4` 則不發；若 `>=4` 且未發過則 send 新公告並寫 `published_messages`。
6. 更新（edit）規則：僅當事件 `>=4` 且已發過、且 `fingerprint` 有變更才 edit；edit 失敗則重發並更新 `message_id` mapping；未 `/setup` 或缺權限則不發不 edit。
7. Poller backoff：連續失敗時指數退避（帶 jitter），成功後重置；可在未設定 backoff 時退回固定 interval。

## Further Considerations

1. 只取 Top 20：若擔心「更新很晚才出現」可再調大 N（但你已定 N=20）。
2. `no-cache` 無法靠 304：用事件 `fingerprint`/`data_hash` 控制是否需要 edit。
3. `<4` 也寫入 seen：可避免之後同一事件在 Top 20 反覆出現造成重複判斷。
4. 只取 Top 20 的取捨：若「上月事件」在月初仍可能更新，但被本月大量事件擠出 Top 20，將無法被偵測到更新（可透過調大 N 緩解）。

---

## 具體規格化重點

### 資料源

- `GET /zh-tw/earthquake/data/`：建立 session（cookies）
- `POST /zh-tw/earthquake/csv`：下載 CSV（`application/x-www-form-urlencoded`）
- CSV：**Big5**、`,` 分隔
- Header：`編號,地震時間,經度,緯度,規模,深度,最大震度,位置`

### event_key 規則（穩健版本）

- 若 `編號` trim 後為純數字：`event_key = "E:" + 編號`
- 否則（例如「小區域有感地震」）：

  `event_key = "H:" + hash(地震時間 + 經度(4位) + 緯度(4位) + 規模(1位) + 深度(1位))`

  （刻意不把「位置文字」放進 key，避免文字修正導致 key 改變）

### intensity 解析與門檻

- 可解析格式：`4`、`5弱`、`5強`、（若出現）`4-`、`4+`
- 門檻：解析後值 **≥ 4** 才允許發送/更新
- 解析失敗：視為 `<4`（不發、不 edit），但仍寫入 seen state

### 發送/更新邏輯（符合你最後決策）

- **所有事件**：先更新 `seen_events`
- **<4**：不發；若以前已發過但本次變 <4 → **不 edit、不刪**（公告保持原樣）
- **≥4 且未發過**：發新公告，寫入 `published_messages`
- **≥4 且已發過**：若 fingerprint 變更才 edit；edit 失敗就重發並更新 mapping

> 補充說明：若某事件初次出現時 `<4`（只寫入 seen），後續修正為 `≥4`，將視為「未發過且達門檻」→ 觸發發送新公告。

---

## 最小設定（env vars）

- `DATA_BASE_URL`（例如 `https://scweb.cwa.gov.tw`）
- `DISCORD_TOKEN`
- `SQLITE_PATH`（例如 `/data/bot.db`，對應 Docker volume）
- `POLL_INTERVAL_SECONDS=60`（可寫死也行）
- `TOP_N=20`（可寫死也行）
- `INTENSITY_THRESHOLD=4`（可寫死也行）
- `BACKOFF_BASE_SECONDS` / `BACKOFF_MAX_SECONDS`（可選，若未設則使用固定 interval 重試）
- `TZ=Asia/Taipei`（建議固定）
- `ALLOWED_GUILD_ID`（可選）：限制 bot 只在指定伺服器允許 `/setup` 生效。

---

## SQLite 最小欄位（只列欄位名）

`seen_events`（含 <4）：

-`event_key`, `event_time`, `first_seen_at`, `last_seen_at`

-`intensity_raw`, `intensity_value`

-`data_hash`（或 `snapshot_hash`）

`published_messages`（只對 ≥4 且已發過）：

-`event_key`, `channel_id`, `message_id`

-`published_at`, `last_edited_at`

-`last_published_hash`

-`status`（可選）

---

## /setup 設定的持久化（建議補齊）

由於頻道是透過 `/setup` 綁定，必須持久化設定，避免重啟容器後遺失。

`settings`（或 `guild_settings`，單伺服器也可只存一列）：

- `guild_id`（可選，若使用 `ALLOWED_GUILD_ID` 可不存）
- `channel_id`
- `enabled`
- `updated_at`

## Progress

- [ ] 0 Project bootstrap
- [ ] 1 Dependencies + config
- [ ] 2 SQLite schema + repo (incl. settings)
- [ ] 3 Discord bot + /setup + /status
- [ ] 4 CWA CSV source (GET+POST, 2 months)
- [ ] 5 CSV parse + normalize
- [ ] 6 Intensity parsing (>=4)
- [ ] 7 event_key + fingerprint
- [ ] 8 Policies (Top20 + publish/edit rules)
- [ ] 9 Poller + backoff
- [ ] 10 Renderer/publisher + edit failover
- [ ] 11 Docker + volume
