# AGENTS.md

## 專案概述

這是一個小型 Flask 應用程式，用來查詢 Yallvend 點數、掃描販賣機 QR Code、查詢商品價格及送出付款。

- `app.py`：Flask 路由（`/`、`/balance`、`/price`、`/pay`）。
- `payment_manager.py`：呼叫外部 Yallvend API。
- `templates/index.html`：完整的 Bootstrap、原生 JavaScript 與 jsQR 前端；介面使用繁體中文。
- `app.wsgi`：Apache/mod_wsgi 正式環境進入點。

## 工作規範

- 不得提交憑證或真實的個人／零食序號。設定應存放於環境變數，並記錄在 `.env.example`。
- 將 `/pay` 與 `PaymentManager.pay()` 視為具有真實扣款副作用的操作。開發或測試時不得呼叫正式付款端點，應模擬 `requests`。
- 除非任務明確要求修改介面契約，否則維持既有的 JSON 回應格式與 QR Code 網址格式。
- 維持目前輕量的專案結構並縮小變更範圍；沒有明確需求時，不要加入新的框架或建置步驟。

## 驗證方式

使用 Python 3.11.2 建立 `venv`、執行 `source venv/bin/activate` 與 `pip install -r requirements.txt`；執行 `python app.py` 在本機啟動。

至少執行：

```sh
PYTHONPYCACHEPREFIX=/tmp/vending-machine-helper-pycache python3 -m py_compile app.py payment_manager.py
python -m unittest discover -s tests
git diff --check
```

修改路由或付款流程時，應使用 Flask 測試用戶端並模擬外部 HTTP 呼叫來加入聚焦的測試；測試不得依賴正式服務。
