# url

- 專案實際網址： https://food.roga.tw
- iPhone 使用 Safari 開啟連結後按「分享」選擇「加入主畫面」即可新增本網站為桌面圖示

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

以下以 Ubuntu/Debian、Apache 2、Python 3.11.2 與 `www-data` 為例。請先確認 DNS 的 `example.com` 已指向這台伺服器，並且防火牆允許 TCP 80/443。

## 1. 安裝系統套件

```bash
sudo apt update
sudo apt install -y apache2 libapache2-mod-wsgi-py3 python3 python3-venv python3-pip git
sudo systemctl enable apache2

python3 --version
apache2ctl -v
```

`python3 --version` 應顯示 `Python 3.11.2`。若版本不同，請先安裝／切換到與正式環境一致的 Python 3.11，再建立虛擬環境；mod_wsgi 與虛擬環境必須使用相同的 Python major/minor 版本。

## 2. 部署專案檔案

```bash
sudo install -d -o "$USER" -g www-data -m 750 /var/www/example.com
git clone https://github.com/roga/vending-machine-helper.git /var/www/example.com
find /var/www/example.com -type d -exec chmod 750 {} \;
find /var/www/example.com -type f -exec chmod 640 {} \;
```

如果目錄已經是既有 checkout，請改為：

```bash
cd /var/www/example.com
git pull --ff-only
```

## 3. 建立虛擬環境與安裝依賴

虛擬環境要使用 Apache/mod_wsgi 所使用的同一個 Python 3.11 版本：

```bash
cd /var/www/example.com
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -c "import flask, requests, dotenv; print('Python dependencies: OK')"
```

## 4. 設定 Yallvend 環境變數

`app.py` 會讀取 `/var/www/example.com/.env`。請使用正式環境的設定值，不要把 `.env` 提交到 Git，也不要在 shell history 中直接輸入憑證：

```bash
cd /var/www/example.com
cp .env.example .env
${EDITOR:-vi} .env
sudo chown root:www-data .env
sudo chmod 640 .env
```

請確認 `.env` 內的 `PLACEHOLDER` 都已替換，而且 Apache 的 `www-data` 使用者可以讀取該檔案。

## 5. 建立 Apache VirtualHost

啟用 WSGI daemon mode，讓這個網站使用自己的程序與虛擬環境：

```bash
sudo tee /etc/apache2/sites-available/example.com.conf > /dev/null <<'APACHE'
<VirtualHost *:80>
    ServerName example.com

    WSGIDaemonProcess example.com \
        user=www-data group=www-data \
        processes=2 threads=5 \
        python-home=/var/www/example.com/venv \
        python-path=/var/www/example.com
    WSGIProcessGroup example.com
    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptAlias / /var/www/example.com/app.wsgi

    <Directory /var/www/example.com>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/example.com-error.log
    CustomLog ${APACHE_LOG_DIR}/example.com-access.log combined
</VirtualHost>
APACHE

sudo a2enmod wsgi
sudo a2ensite example.com.conf
sudo a2dissite 000-default.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

`configtest` 必須顯示 `Syntax OK`。`python-home` 指向虛擬環境根目錄，不要指向 `venv/bin/python`。

## 6. 驗證 Apache 與 Flask

先從伺服器本機測試 VirtualHost：

```bash
curl --fail --silent --show-error \
  -H 'Host: example.com' \
  http://127.0.0.1/ | head

sudo systemctl status apache2 --no-pager
sudo journalctl -u apache2 -n 100 --no-pager
sudo tail -n 100 /var/log/apache2/example.com-error.log
```

確認首頁正常後，再從外部瀏覽器開啟 `http://example.com/`。不要用 `curl` 測試 `/pay`，因為它會產生真實付款副作用。

## 7. 啟用 HTTPS

相機掃描功能需要 HTTPS。確認 DNS 與 HTTP 已正常後，使用 Certbot 讓它自動修改 Apache 設定：

```bash
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d example.com
sudo certbot renew --dry-run
```

完成後請確認 `https://example.com/` 與相機權限都正常。

## 8. 更新部署

之後發布新版本時，在伺服器執行：

```bash
cd /var/www/example.com
git pull --ff-only
venv/bin/python -m pip install -r requirements.txt
sudo apache2ctl configtest
sudo systemctl reload apache2
```

若更新後發生問題，先查看 `/var/log/apache2/example.com-error.log`，確認原因後再回復到上一個 Git commit。

參考：[mod_wsgi daemon mode 與 virtualenv](https://www.modwsgi.org/en/develop/user-guides/virtual-environments.html)、[WSGIDaemonProcess](https://www.modwsgi.org/en/develop/configuration-directives/WSGIDaemonProcess.html)、[Certbot Apache plugin](https://certbot.eff.org/instructions?os=ubuntubionic&ws=apache)

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
