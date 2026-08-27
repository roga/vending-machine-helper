## Overview

在維持 Flask 單頁應用與無前端建置流程的前提下，讓 repository 的 Python 版本宣告與正式主機的 Python 3.11.2 一致、更新前端依賴宣告，修正付款金額信任前端、QR Code 內容注入、錯誤回應失真及敏感序號出現在網址等問題，並用少量自動化測試保護付款流程。正式主機與 mod_wsgi 的實際調整不在本提案的執行範圍內，只記錄必要的部署提醒。

## Scope

- `.python-version`: 新增 repository 使用的 Python 3.11.2 版本宣告，使其與正式主機一致。
- `requirements.txt`: 僅保留並更新直接依賴，加入程式實際使用的 `requests`，移除不再需要的 Flask-CORS 與手動鎖定的間接依賴。
- `app.py`: 移除全域 CORS、驗證輸入、讓付款價格由後端查詢、回傳正確的 HTTP 錯誤狀態，並避免在餘額介面暴露序號。
- `payment_manager.py`: 統一外部 API 失敗處理、驗證回應內容，並保持所有外部呼叫可被測試模擬。
- `templates/index.html`: 使用相對網址與本地靜態資源路徑、更新並鎖定前端依賴、避免不受信任內容插入 HTML，並以原生瀏覽器 API 取代 jQuery。
- `tests/test_app.py`: 新增聚焦於路由、付款價格、安全輸出與外部服務失敗的測試；所有外部 HTTP 呼叫均須模擬。
- `README.md`: 更新 Python 3.11.2、本機執行、測試方式及 mod_wsgi 必須使用相符 Python 版本的部署提醒。

## Requirements

- [V] R1: 以 `.python-version` 與 README 將 repository 的目標執行版本設為 Python 3.11.2，並明確說明正式環境的 mod_wsgi 必須以相符的 Python 3.11 版本建置。
- [V] R2: 將 `requirements.txt` 精簡為直接依賴，使用 Flask 3.1.3、python-dotenv 1.2.3 與 requests 2.34.2，移除 Flask-CORS 及 Flask 的間接依賴項目。
- [V] R3: 將前端 API 與圖片改用同源相對路徑或 Flask 產生的靜態路徑，並從後端移除全域 CORS 設定。
- [V] R4: 修改付款介面，使客戶端只提交零食序號與販賣機 ID；後端必須重新查詢目前價格，且只能以該後端價格呼叫付款 API。
- [V] R5: 在後端驗證零食序號與販賣機 ID 的必要格式和合理長度，無效輸入不得送往外部 API。
- [V] R6: 顯示販賣機 ID、價格或 QR Code 掃描內容時，不得以字串拼接方式將不受信任資料插入 HTML。
- [V] R7: 外部 API 連線、HTTP 狀態、JSON 格式或必要欄位發生錯誤時，後端須回傳適當的 502 回應且不得洩漏內部網址、憑證或完整例外內容；前端不得把失敗回應顯示為購買成功。
- [V] R8: 將餘額查詢改為 POST，零食序號不得出現在查詢字串或回應內容中。
- [V] R9: 將 Bootstrap 更新並鎖定至 5.3.8、將 jsQR 鎖定至 1.4.0，並以原生 DOM、事件、`fetch` 與 `async`/`await` 取代 jQuery，且不新增前端建置步驟。
- [V] R10: 使用 Flask test client 與 Python 標準函式庫的 mock 新增自動化測試，覆蓋必要參數、後端決定付款價格、外部 API 失敗、餘額查詢及不受信任輸入；測試不得連線至正式服務。
- [V] R11: 更新 README 的環境建立、啟動與測試指令，使其與新的 Python 版本、依賴清單及測試方式一致。

## Acceptance Criteria

- [ ] AC1: Scenario: 使用 Python 3.11.2 依 `requirements.txt` 安裝後，可以匯入並啟動 Flask 應用；環境中不需要 Flask-CORS，且 `requests` 由專案明確宣告。
- [V] AC2: Scenario: 從本機或正式網域開啟首頁時，圖片與 `/balance`、`/price`、`/pay` 都使用目前網域；頁面不載入 jQuery，Bootstrap 與 jsQR 使用指定版本。
  Evidence: `test_frontend_uses_pinned_native_dependencies` 通過；`rg` 確認前端使用相對 `fetch`、Flask `url_for`、Bootstrap 5.3.8 與 jsQR 1.4.0，且沒有 jQuery 或正式網域 API URL。
- [V] AC3: Scenario: 客戶端嘗試自行提供或竄改價格時，付款 API 不採用該值，實際付款呼叫只收到後端依販賣機 ID 查得的價格。
  Evidence: `test_pay_uses_server_price_not_client_price` 通過；測試提供價格 `1` 但確認付款 mock 收到後端查得的 `25`。
- [V] AC4: Scenario: 缺少、過長或格式不符的零食序號或販賣機 ID 會收到 400，且模擬的外部 API 不會被呼叫。
  Evidence: 臨時 Flask test client 檢查空資料、缺少欄位、129 字元序號與 HTML 內容，全部回傳 400 且 `requests.post` 未被呼叫。
- [V] AC5: Scenario: 掃描內容包含 HTML 或 JavaScript 片段時，頁面只將其視為文字或拒絕該格式，不會建立可執行的 DOM 內容。
  Evidence: 靜態檢查確認模板沒有 `.html()`、`innerHTML` 或 `outerHTML`；QR Code 以嚴格格式比對，顯示內容使用 `textContent` 與 `replaceChildren`。
- [V] AC6: Scenario: 任一外部 Yallvend 呼叫逾時、回傳非成功狀態、無效 JSON 或缺少必要欄位時，路由回傳不含敏感細節的 502，前端顯示失敗而非成功。
  Evidence: `test_external_failure_returns_generic_502` 與 `test_failed_payment_status_is_not_success` 通過；程式碼檢查確認外部錯誤統一轉為 502，前端檢查 `response.ok` 與成功狀態。
- [V] AC7: Scenario: 查詢餘額時，零食序號只存在 POST request body，不出現在 URL 或 JSON response。
  Evidence: `test_balance_uses_post_and_does_not_echo_code` 通過；路由只接受 POST，前端以 `URLSearchParams` 放入 request body，回應僅包含 balance。
- [V] AC8: Scenario: 執行專案記載的自動化測試、Python 語法檢查與 `git diff --check` 全部通過，且測試過程沒有對正式服務發出網路請求。
  Evidence: `venv/bin/python -m unittest discover -s tests -v` 6/6 通過；Python 編譯與 `git diff --check` 通過；測試中的所有 outbound HTTP 均以 `@patch('payment_manager.requests.post')` 模擬。
