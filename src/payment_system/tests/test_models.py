from unittest import TestCase

from django.contrib.auth.models import User

from payment_system.models import PaymentTransaction, Account, Currency
from payment_system.management.commands.add_init_data import Command as InitData
from payment_system import settings


class TestModels(TestCase):

    def setUp(self):
        InitData().handle()
        self.alan = User.objects.create_user(username='alan', password='1')
        self.joseph = User.objects.create_user(username='joseph', password='1')
        self.alan_acc_u1 = Account.objects.create(
            type=Account.types.USER_ACCOUNT,
            user=self.alan,
            currency=Currency.objects.get(slug='USD'),
            amount=100,
        )
        self.alan_acc_u2 = Account.objects.create(
            type=Account.types.USER_ACCOUNT,
            user=self.alan,
            currency=Currency.objects.get(slug='USD'),
            amount=100,
        )
        self.alan_acc_e = Account.objects.create(
            type=Account.types.USER_ACCOUNT,
            user=self.alan,
            currency=Currency.objects.get(slug='EUR'),
            amount=100,
        )
        self.joseph_acc_c = Account.objects.create(
            type=Account.types.USER_ACCOUNT,
            user=self.joseph,
            currency=Currency.objects.get(slug='CNY'),
            amount=100,
        )
        self.joseph_acc_r = Account.objects.create(
            type=Account.types.USER_ACCOUNT,
            user=self.joseph,
            currency=Currency.objects.get(slug='RUB'),
            amount=100,
        )

    def test_add_transaction(self):
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_u2, False, 5)
        self.assertEqual(transaction.source, self.alan_acc_u1)
        self.assertEqual(transaction.destination, self.alan_acc_u2)
        self.assertEqual(transaction.status, PaymentTransaction.statuses.SCHEDULED)
