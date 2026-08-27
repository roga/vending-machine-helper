from decimal import Decimal, InvalidOperation
import os
import re

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from payment_manager import PaymentManager, PaymentManagerError

load_dotenv(dotenv_path="/var/www/food.roga.tw/.env")

app = Flask(__name__)

TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9._-]{1,128}$')
PAYMENT_SUCCESS_STATUSES = {'success', 'ok', 'paid', 'completed', 'true', '1'}


def _get_input(name):
    data = request.get_json(silent=True) or {}
    return request.form.get(name) or data.get(name)


def _valid_token(value):
    return isinstance(value, str) and bool(TOKEN_PATTERN.fullmatch(value.strip()))


def _valid_price(value):
    try:
        amount = Decimal(str(value))
        return amount.is_finite() and amount > 0
    except (InvalidOperation, TypeError, ValueError):
        return False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/balance', methods=['POST'])
def check_balance():
    code = _get_input('code')
    if not _valid_token(code):
        return jsonify({'error': 'Invalid code'}), 400
    code = code.strip()
    try:
        result = PaymentManager(code).get_balance()
    except PaymentManagerError:
        return jsonify({'error': 'Balance service unavailable'}), 502
    return jsonify({'balance': result})


@app.route('/price', methods=['GET'])
def check_price():
    vid = request.args.get('vid', '').strip()
    if not _valid_token(vid):
        return jsonify({'error': 'Invalid vending machine ID'}), 400
    try:
        result = PaymentManager('dummy').get_current_product_price(vid)
    except PaymentManagerError:
        return jsonify({'error': 'Price service unavailable'}), 502
    if not _valid_price(result):
        return jsonify({'error': 'Invalid price response'}), 502
    return jsonify({'vid': vid, 'price': result})


@app.route('/pay', methods=['POST'])
def pay_product():
    code = _get_input('code')
    vid = _get_input('vid')
    if not _valid_token(code) or not _valid_token(vid):
        return jsonify({'error': 'Invalid code or vending machine ID'}), 400
    code = code.strip()
    vid = vid.strip()

    pm = PaymentManager(code)
    try:
        price = pm.get_current_product_price(vid)
        if not _valid_price(price):
            raise PaymentManagerError('Invalid price response')
        result = str(pm.pay(price, vid)).lower()
    except PaymentManagerError:
        return jsonify({'error': 'Payment service unavailable'}), 502

    if result not in PAYMENT_SUCCESS_STATUSES:
        return jsonify({'error': 'Payment failed'}), 502
    return jsonify({'vid': vid, 'price': price, 'result': result})


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
