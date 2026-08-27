import json
import os
import unittest
from unittest.mock import Mock, patch

import requests

from app import app


def api_response(payload):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.env = patch.dict(os.environ, {
            'YALLVEND_API_BALANCE_URL': 'https://example.test/balance',
            'YALLVEND_API_PRODUCT_PRICE_URL': 'https://example.test/price',
            'YALLVEND_API_PAYMENT_URL': 'https://example.test/pay',
            'YALLVEND_API_KEY': 'test-key',
            'YALLVEND_PRICE_KEY': 'test-price-key',
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    @patch('payment_manager.requests.post')
    def test_balance_uses_post_and_does_not_echo_code(self, post):
        post.return_value = api_response({'point': '42.8'})

        response = self.client.post('/balance', data={'code': 'snack-01'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'balance': 42})
        self.assertNotIn(b'snack-01', response.data)
        self.assertEqual(post.call_args.kwargs['json']['id'], 'snack-01')

    @patch('payment_manager.requests.post')
    def test_invalid_input_is_rejected_before_external_call(self, post):
        response = self.client.post('/pay', data={'code': 'ok', 'vid': '<script>'})

        self.assertEqual(response.status_code, 400)
        post.assert_not_called()

    @patch('payment_manager.requests.post')
    def test_pay_uses_server_price_not_client_price(self, post):
        post.side_effect = [
            api_response({'defaultAmount': '25'}),
            api_response({'status': 'success'}),
        ]

        response = self.client.post('/pay', data={
            'code': 'snack-01',
            'vid': 'VM-01',
            'price': '1',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['price'], '25')
        payment_payload = json.loads(post.call_args_list[1].kwargs['data']['data'])
        self.assertEqual(payment_payload['amount'], '25')

    @patch('payment_manager.requests.post')
    def test_external_failure_returns_generic_502(self, post):
        post.side_effect = requests.Timeout('secret endpoint details')

        response = self.client.post('/balance', data={'code': 'snack-01'})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json, {'error': 'Balance service unavailable'})
        self.assertNotIn(b'secret endpoint details', response.data)

    @patch('payment_manager.requests.post')
    def test_failed_payment_status_is_not_success(self, post):
        post.side_effect = [
            api_response({'defaultAmount': 25}),
            api_response({'status': 'failed'}),
        ]

        response = self.client.post('/pay', data={'code': 'snack-01', 'vid': 'VM-01'})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json, {'error': 'Payment failed'})

    def test_frontend_uses_pinned_native_dependencies(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'jquery', response.data.lower())
        self.assertIn(b'bootstrap@5.3.8', response.data)
        self.assertIn(b'jsqr@1.4.0', response.data.lower())


if __name__ == '__main__':
    unittest.main()
