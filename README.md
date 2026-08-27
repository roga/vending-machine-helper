# url

- 網址： https://food.roga.tw/
- iPhone 使用 Safari 開啟後按「分享」選擇「加入主畫面」即可新增本網站為桌面圖示

# vending-machine-helper

- 顯示目前點數餘額
- 掃描販賣機上的 QR Code 支付點數
- 在裝置的本地端 (Web Storage) 儲存零食序號，且支援修改

# screenshot

<img src="https://github.com/user-attachments/assets/6d1617f1-eaa7-455b-a774-203ea773c0c2" style="width: 200px;">
<img src="https://github.com/user-attachments/assets/5b2014bb-294e-4d33-b332-7061cf2ffb3f" style="width: 200px;">
<img src="https://github.com/user-attachments/assets/cb5c8d3f-767a-40b1-879a-ec8d6478b450" style="width: 200px;">
<img src="https://github.com/user-attachments/assets/714ab6c1-3442-433d-ab25-7e9baeb53939" style="width: 200px;">

# production env

- Apache + mod_wsgi
- mod_wsgi 必須使用與正式主機相符的 Python 3.11 版本建置

# restart server

sudo systemctl restart apache2

# development env

請先在專案根目錄執行以下指令。正式的 Yallvend 設定與零食序號不要提交到 Git。

```bash
# 進入專案目錄（請替換成你的本機路徑）
cd /path/to/vending-machine-helper

# 確認本機使用 Python 3.11
python3.11 --version

# 建立並啟用虛擬環境
python3.11 -m venv venv
source venv/bin/activate

# 安裝專案依賴
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 執行測試（不會呼叫正式服務）
python -m unittest discover -s tests -v

# 若要測試餘額、價格或付款 API，先建立本機設定檔並填入實際測試設定
cp -n .env.example .env
${EDITOR:-vi} .env

# 將 .env 載入目前 shell；請確認檔案內沒有未替換的 PLACEHOLDER
set -a
source .env
set +a

# 啟動本機 Flask 服務
export FLASK_DEBUG=1
python app.py
```

服務啟動後會監聽 `http://127.0.0.1:5000`。請保留這個終端機讓服務持續執行，再開另一個終端機驗證首頁：

```bash
curl --fail http://127.0.0.1:5000/
```

停止服務請在執行中的終端機按 `Ctrl-C`；離開虛擬環境則執行：

```bash
deactivate
```
