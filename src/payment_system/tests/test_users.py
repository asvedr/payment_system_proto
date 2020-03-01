from django.contrib.auth.models import User
from django.test import TestCase

from payment_system.management.commands.add_init_data import Command as InitData
from payment_system.models import Account
from tests.common import JsonClient


class TestUsers(TestCase):

    def setUp(self):
        InitData().handle()
        User.objects.create_user(username='foo', password='bar', email='foo@bar.com', is_active=True)
        self.client = JsonClient()

    def test_get_token(self):
        response = self.client.post('/login/', {'username': 'foo', 'password': 'bar'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['token'])

    def test_sign_in(self):
        response = self.client.post('/sign_in/', {'username': 'x', 'password': 'y'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.get(username='x'))
        self.assertEqual(
            {
                'USD': 100,
                'EUR': 0,
                'CNY': 0,
            },
            dict(Account.objects.filter(user__username='x').values_list('currency__slug', 'amount'))
        )
