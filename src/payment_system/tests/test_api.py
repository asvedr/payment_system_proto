from django.contrib.auth.models import User
from django.test import TestCase

from payment_system import models, tasks
from payment_system.management.commands.add_init_data import Command as InitData

from tests.common import JsonClient


class BaseTestApi(TestCase):

    def setUp(self):
        InitData().handle()
        self.client = JsonClient()
        self.client.json_post('/sign_in/', {'username': 'alan', 'password': '1'})
        self.client.json_post('/sign_in/', {'username': 'joseph', 'password': '1'})
        (
            models.Account.objects
                .filter(user__username='alan', currency__slug='EUR')
                .update(amount=100)
        )
        response = self.client.post('/login/', {'username': 'alan', 'password': '1'})
        self.client.token = response.json()['token']
        self.alan = User.objects.get(username='alan')


class TestApi(BaseTestApi):

    def test_check_balance(self):
        response = self.client.get('/check_balance/')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()['result']
        for item in response_data:
            del item['id']
        self.assertEqual(
            [
                {'currency': 'USD', 'description': 'USA United States Dollar', 'amount': '100.00'},
                {'currency': 'EUR', 'description': 'European Euro', 'amount': '100.00'},
                {'currency': 'CNY', 'description': 'Chinese Yuán', 'amount': '0.00'},
            ],
            response_data
        )

    def test_request_transaction(self):
        acc1 = models.Account.objects.get(user__username='alan', currency__slug='EUR')
        acc2 = models.Account.objects.get(user__username='joseph', currency__slug='USD')
        response = self.client.json_post('/request-transaction/', {
            'source': acc1.id,
            'destination': acc2.id,
            'amount': '10',
        })
        self.assertEqual(response.status_code, 200)
        response_data = response.json()['result']
        del response_data['id']
        del response_data['created_at']
        self.assertEqual(
            {
                'source': acc1.id,
                'destination': acc2.id,
                'status': 'scheduled',
                'taxes': '0.00',
                'exchange': [],
                'amount': '10.00',
                'currency': 'USD',
                'processed_at': None,
                'spent': '0.00',
            },
            response_data
        )


class TestGetTransaction(BaseTestApi):

    def setUp(self):
        super().setUp()
        self.acc1 = models.Account.objects.get(user__username='alan', currency__slug='EUR')
        self.acc2 = models.Account.objects.get(user__username='joseph', currency__slug='USD')
        self.transaction1 = models.PaymentTransaction.objects.request(self.acc1, self.acc2, True, 30)
        self.transaction2 = models.PaymentTransaction.objects.request(self.acc2, self.acc1, True, 20)
        self.transaction3 = models.PaymentTransaction.objects.request(self.acc1, self.acc2, True, 10)
        self.transaction4 = models.PaymentTransaction.objects.request(self.acc2, self.acc1, True, 999)
        tasks.complete_transactions()

    def test_outgoing_ordering(self):
        for transaction in [self.transaction1, self.transaction2, self.transaction3]:
            transaction.refresh_from_db()
        response = self.client.get('/outgoing/?ordering=created_at')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for row in data:
            del row['processed_at']
            del row['created_at']
            del row['exchange'][0]['time']
        self.assertEqual(
            [
                {
                    'id': self.transaction1.id,
                    'source': self.acc1.id,
                    'destination': self.acc2.id,
                    'status': 'completed',
                    'taxes': '3.00',
                    'exchange': [{
                        'source': 'EUR',
                        'destination': 'USD',
                        'rate': '1.10',
                    }],
                    'spent': '36.30',
                    'amount': '30.00',
                    'currency': 'USD',
                },
                {
                    'id': self.transaction3.id,
                    'source': self.acc1.id,
                    'destination': self.acc2.id,
                    'status': 'completed',
                    'taxes': '1.00',
                    'exchange': [{
                        'source': 'EUR',
                        'destination': 'USD',
                        'rate': '1.10',
                    }],
                    'spent': '12.10',
                    'amount': '10.00',
                    'currency': 'USD',
                }
            ],
            data
        )
        response = self.client.get('/outgoing/?ordering=amount')
        self.assertEqual(response.status_code, 200)
        id_list = [row['id'] for row in response.json()]
        self.assertEqual([self.transaction3.id, self.transaction1.id], id_list)

    def test_filters_outgoing(self):
        response = self.client.get('/outgoing/?amount=30')
        self.assertEqual(response.status_code, 200)
        id_list = [row['id'] for row in response.json()]
        self.assertEqual([self.transaction1.id], id_list)

    def test_incoming_transactions(self):
        response = self.client.get('/incoming/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for row in data:
            del row['processed_at']
            del row['created_at']
        self.assertEqual(
            [{
                'id': self.transaction2.id,
                'source': self.acc2.id,
                'destination': self.acc1.id,
                'amount': '20.00',
                'currency': 'EUR',
            }],
            data
        )

