import json
import os
import requests


class PaymentManagerError(Exception):
    """Raised when a Yallvend request cannot be completed safely."""


class PaymentManager:
    def __init__(self, personal_code):
        self.personal_code = personal_code

        self._api_get_balance_url = os.environ.get('YALLVEND_API_BALANCE_URL')
        self._api_product_price_url = os.environ.get('YALLVEND_API_PRODUCT_PRICE_URL')
        self._api_payment_url = os.environ.get('YALLVEND_API_PAYMENT_URL')
        self._api_get_balance_referer = os.environ.get('YALLVEND_REFERER_BALANCE')
        self._api_payment_referer_base = os.environ.get('YALLVEND_REFERER_PAYMENT_BASE')

        self._api_key_balance = os.environ.get('YALLVEND_API_KEY')
        self._api_key_price = os.environ.get('YALLVEND_PRICE_KEY')

    @staticmethod
    def _post_json(url, **kwargs):
        if not url:
            raise PaymentManagerError('外部服務未設定')
        try:
            response = requests.post(url, timeout=5, **kwargs)
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError, TypeError) as exc:
            raise PaymentManagerError('外部服務暫時無法使用') from exc
        if not isinstance(result, dict):
            raise PaymentManagerError('外部服務回應格式錯誤')
        return result

    def get_balance(self):
        headers = {'Content-Type': 'application/json'}
        if self._api_get_balance_referer:
            headers['Referer'] = self._api_get_balance_referer
        payload = {
            'country': 'tw',
            'key': self._api_key_balance,
            'id': self.personal_code
        }
        result = self._post_json(self._api_get_balance_url, json=payload, headers=headers)
        try:
            return int(float(result['point']))
        except (KeyError, TypeError, ValueError) as exc:
            raise PaymentManagerError('外部服務回應格式錯誤') from exc

    def get_current_product_price(self, vid):
        form_data = {
            'key': self._api_key_price,
            'func': 'loadDefaultAmount',
            'vidCode': vid
        }
        result = self._post_json(self._api_product_price_url, data=form_data)
        if 'defaultAmount' not in result:
            raise PaymentManagerError('外部服務回應格式錯誤')
        return result['defaultAmount']

    def pay(self, price, vid):
        data = {
            'vid': vid,
            'amount': str(price),
            'staff_id': self.personal_code,
            'uuid': '111',
            'haveAuth': False
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        if self._api_payment_referer_base:
            headers['Referer'] = self._api_payment_referer_base + vid
        result = self._post_json(
            self._api_payment_url,
            data={'data': json.dumps(data)},
            headers=headers
        )
        if 'status' not in result:
            raise PaymentManagerError('外部服務回應格式錯誤')
        return result['status']
