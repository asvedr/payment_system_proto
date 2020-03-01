from django.contrib.auth.models import User
from django.test import TestCase

from payment_system import models
from payment_system.management.commands.add_init_data import Command as InitData

from tests.common import JsonClient


class TestApi(TestCase):

    def setUp(self):
        InitData().handle()
        self.client = JsonClient()
        self.client.json_post('/sign_in/', {'username': 'alan', 'password': '1'})
        self.client.json_post('/sign_in/', {'username': 'joseph', 'password': '1'})
        response = self.client.post('/login/', {'username': 'alan', 'password': '1'})
        self.client.token = response.json()['token']
        self.alan = User.objects.get(username='alan')

    def test_check_balance(self):
        response = self.client.get('/check_balance/')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()['result']
        for item in response_data:
            del item['id']
        self.assertEqual(
            [
                {'currency': 'USD', 'description': 'USA United States Dollar', 'amount': '100.00'},
                {'currency': 'EUR', 'description': 'European Euro', 'amount': '0.00'},
                {'currency': 'CNY', 'description': 'Chinese Yuán', 'amount': '0.00'},
            ],
            response_data
        )

    def test_request_transaction(self):
        acc1 = models.Account.objects.get(user__username='alan', currency__slug='EUR')
        acc2 = models.Account.objects.get(user__username='joseph', currency__slug='USD')
        response = self.client.json_post('/transactions/', {
            'source': acc1.id,
            'destination': acc2.id,
            'amount': '10',
        })
        import ipdb; ipdb.set_trace()
        self.assertEqual(response.status_code, 200)
