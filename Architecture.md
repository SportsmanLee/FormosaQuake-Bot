## Architecture: EEW_DiscordBot（公告版，易擴充/易維護）

> 本文件描述「程式架構與模組責任」；對應的行為/規格請參考 `Spec.md`。

### Goals
- **易擴充**：未來加入 EEW 或其他資料源，不影響主流程與 Discord 發送邏輯。
- **易維護**：把「抓資料」「解析/正規化」「規則（門檻/取樣）」「狀態（SQLite）」「Discord 發送」分離。
- **可測試**：核心規則與解析不依賴網路/Discord，可用固定樣本檔做回歸測試。

---

## High-level Dataflow
1. Scheduler 每 60s 觸發一次 pipeline（失敗時可指數退避）
2. Source layer 取得「本月 + 上月」CSV（Big5）
3. Parser/Normalizer 解析 CSV → 產生標準化事件 `EarthquakeEvent`
4. Selector 合併/去重/排序 → Top N=20
5. Policy 決策：更新 seen（所有事件）、判斷門檻（>=4）、判斷是否 send/edit
6. Store 寫入 SQLite（settings / seen / published mappings）
7. Notifier 對 Discord 發送（send/edit）

---

## Layered Design（推薦分層）

### 1) Domain（純資料模型與規則，最穩定）
**目的**：集中管理所有「可測」的核心邏輯，不碰 HTTP/Discord/DB。

- `EarthquakeEvent`
  - `event_key`（穩健鍵：E:編號 / H:hash）
  - `event_time`（Asia/Taipei）
  - `lon`, `lat`, `magnitude`, `depth_km`
  - `intensity_raw`, `intensity_value`
  - `location_text`
  - `source`（例如 `cwa_csv`）

- `parse_intensity(raw) -> intensity_value`
  - 支援：`4`, `5弱`, `5強`, `4-`, `4+` …

- `build_event_key(row/event) -> str`
  - EventNo（trim 後純數字）優先
  - 否則使用時間+座標+規模+深度組合 hash

- `fingerprint(event) -> str`
  - 用於判斷同一事件是否更新（比對關鍵欄位）

**為什麼這樣拆**：
- EEW 加進來時，只要產生同樣的 `EarthquakeEvent`，後續流程完全共用。

---

### 2) Source（資料來源：可插拔）
**目的**：把「怎麼拿到資料」封裝起來，避免 pipeline 直接處理 cookies/session。

介面（概念）：
- `fetch_month_csv(year, month) -> bytes`

> 實作建議：Source 先回傳原始 `bytes`（CSV 檔內容），把 Big5 解碼與 CSV parsing 統一放在 Parsing/Normalization 層，避免 Source 層與格式耦合。

實作：
- `CwaCsvSource`
  - `GET /zh-tw/earthquake/data/` 建 session
  - `POST /zh-tw/earthquake/csv` 下載 Big5 CSV
  - cookie jar 常駐、固定 UA/Origin/Referer

未來擴充：
- `CwaEewSource`（或其他 EEW 來源）只要輸出同一 domain model。

---

### 3) Parsing/Normalization（解析與正規化）
**目的**：把 Big5 CSV → 乾淨資料結構，並統一格式。

- `decode_big5(bytes) -> str`
- `parse_csv(text) -> list[RawRow]`
- `normalize_row(row) -> EarthquakeEvent`

回歸測試來源：
- 用固定的下載 CSV 範例檔（像你目前的檔案）當測試資料。

---

### 4) Policy（規則/策略）
**目的**：把可變需求集中，避免散落 if-else。

- `SelectionPolicy`
  - 合併本月+上月
  - 去重、排序
  - 取 Top N=20

- `ThresholdPolicy`
  - intensity >= 4 才允許 publish/edit

- `PublishPolicy`（對應你最終決策）
  - 所有事件都寫 seen
  - <4 不 publish、不 edit
  - >=4 且未發過 → send
  - >=4 且已發過且 fingerprint 變更 → edit
  - 已發過但變 <4 → 不 edit、不刪

---

### 5) Store（狀態持久化：SQLite）
**目的**：集中管理 DB schema 與查詢，讓其餘層只呼叫 repository。

Repository 介面（概念）：
- `upsert_seen(event_key, event_time, intensity_raw, intensity_value, data_hash, ...)`
- `get_published(event_key) -> PublishedMessage | None`
- `upsert_published(event_key, channel_id, message_id, last_published_hash, ...)`

表設計參考規格書：
- `settings`（單伺服器：公告頻道綁定、啟用狀態；可選 guild id gate）
- `seen_events`
- `published_messages`

注意：
- DB 檔案放 `/data/bot.db` 並以 Docker volume 持久化。

---

### 6) Notifier（Discord）
**目的**：把 Discord API / rate limit / 權限檢查隔離，讓 pipeline 只管「要送什麼」。

- `Renderer`
  - `render_embed(event) -> payload`（統一格式、顏色、欄位）

- `Publisher`
  - `send(channel_id, payload) -> message_id`
  - `edit(channel_id, message_id, payload)`
  - edit 失敗：回傳可辨識錯誤，讓 pipeline 走「重發 + 更新 mapping」

- `Commands`
  - `/setup`：綁定公告頻道（單伺服器）
  -（可選）`/status`：顯示目前設定與最近一次抓取狀態

---

## Error Handling & Resilience
- **來源錯誤**：timeout/5xx/429 → 指數退避（帶 jitter）；必要時重建 session（再 GET data/）
- **解析錯誤**：Big5 解碼或欄位缺失 → 只記錄 log，不發錯誤公告
- **Discord 錯誤**：
  - 缺權限/找不到頻道/訊息被刪：不崩潰；edit 失敗就重發並更新 mapping
- **未 /setup**：完全不發，但仍維護 seen state，避免設定後瞬間重播一堆舊事件

---

## Observability（建議）
- structured logs（至少包含）：`event_key`, `intensity_value`, `action=skip|send|edit`, `reason`
- 重要計數：連續失敗次數、上次成功抓取時間、上次發送/編輯時間

---

## Extension Points（未來加 EEW 的最小改動）
- 新增 `sources/cwa_eew.py`（或其他 EEW source）
- 新增 EEW 專用 `Renderer`（內容格式不同）或在同 renderer 內分支
- 規則層增加 `EventType`（report vs eew）與對應門檻/路由
- DB 可新增欄位 `event_type`，或以 `source` 區分

> 核心 pipeline 不需要改：只要 EEW 也輸出 `EarthquakeEvent`（或相容事件模型）即可。

---

## Suggested Project Structure (Python)
- `src/`
  - `app.py`（entrypoint）
  - `config.py`
  - `domain/`（models, intensity, keys, fingerprint）
  - `sources/`（base, cwa_csv, future cwa_eew）
  - `parsing/`（csv_parser, normalizer）
  - `policies/`（selection, threshold, publish）
  - `store/`（repo, schema init）
  - `notifier/`（discord_client, commands, renderer, publisher）
  - `service/`（poller, pipeline）

（以上為建議拆分，實作時可先合併成較少檔案，等穩定再拆。）
