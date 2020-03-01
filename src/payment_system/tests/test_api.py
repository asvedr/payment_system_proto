from django.contrib.auth.models import User
from django.test import TestCase

from payment_system.management.commands.add_init_data import Command as InitData

from tests.common import JsonClient


class TestApi(TestCase):

    def setUp(self):
        InitData().handle()
        self.client = JsonClient()
        self.client.post('/sign_in/', {'username': 'alan', 'password': '1'})
        response = self.client.post('/login/', {'username': 'alan', 'password': '1'})
        self.client.token = response.json()['token']
        self.alan = User.objects.get(username='alan')

    def test_check_balance(self):
        response = self.client.get('/check_balance/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                {'currency': 'USD', 'description': 'USA United States Dollar', 'amount': '100.00'},
                {'currency': 'EUR', 'description': 'European Euro', 'amount': '0.00'},
                {'currency': 'CNY', 'description': 'Chinese Yuán', 'amount': '0.00'},
            ],
            response.json()['result']
        )
