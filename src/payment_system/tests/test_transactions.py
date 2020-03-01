from unittest import TestCase

from django.contrib.auth.models import User

from payment_system.models import PaymentTransaction, Account, Currency, ExchangeRate
from payment_system.management.commands.add_init_data import Command as InitData
from payment_system.tasks import collect_taxes
from payment_system import settings


class TestTransactions(TestCase):

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
        self.alan_acc_c = Account.objects.create(
            type=Account.types.USER_ACCOUNT,
            user=self.alan,
            currency=Currency.objects.get(slug='CNY'),
            amount=100,
        )

    def tearDown(self):
        PaymentTransaction.objects.all().delete()

    def test_add_transaction(self):
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_u2, False, 5)
        self.assertEqual(transaction.source, self.alan_acc_u1)
        self.assertEqual(transaction.destination, self.alan_acc_u2)
        self.assertEqual(transaction.status, PaymentTransaction.statuses.SCHEDULED)

    def test_complete_transaction_noexchange_notaxes(self):
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_u2, False, 5)
        transaction.complete()
        transaction.refresh_from_db()
        self.alan_acc_u1.refresh_from_db()
        self.alan_acc_u2.refresh_from_db()
        self.assertEqual(transaction.status, PaymentTransaction.statuses.COMPLETED)
        self.assertEqual(self.alan_acc_u1.amount, 95)
        self.assertEqual(self.alan_acc_u2.amount, 105)

    def test_reject_transaction(self):
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_u2, False, 200)
        transaction.complete()
        transaction.refresh_from_db()
        self.alan_acc_u1.refresh_from_db()
        self.alan_acc_u2.refresh_from_db()
        self.assertEqual(transaction.status, PaymentTransaction.statuses.REJECTED)
        self.assertEqual(self.alan_acc_u1.amount, 100)
        self.assertEqual(self.alan_acc_u2.amount, 100)

    def test_complete_transaction_noexchange_taxes(self):
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_u2, True, 10)
        transaction.complete()
        transaction.refresh_from_db()
        self.alan_acc_u1.refresh_from_db()
        self.alan_acc_u2.refresh_from_db()
        taxes_account = Account.objects.get(type=Account.types.TAXES_ACCOUNT, currency__slug='USD')
        self.assertEqual(transaction.status, PaymentTransaction.statuses.USER_MONEY_TRANSMITTED)
        self.assertEqual(self.alan_acc_u1.amount, 89)
        self.assertEqual(self.alan_acc_u2.amount, 110)
        self.assertEqual(taxes_account.amount, 0)

        collect_taxes()
        transaction.refresh_from_db()
        self.alan_acc_u1.refresh_from_db()
        self.alan_acc_u2.refresh_from_db()
        taxes_account.refresh_from_db()

        self.assertEqual(transaction.status, PaymentTransaction.statuses.COMPLETED)
        self.assertEqual(self.alan_acc_u1.amount, 89)
        self.assertEqual(self.alan_acc_u2.amount, 110)
        self.assertEqual(taxes_account.amount, 1)

    def test_complete_transaction_exchange_notaxes(self):
        ExchangeRate.objects.create(
            source=Currency.objects.get(slug='USD'),
            destination=Currency.objects.get(slug='EUR'),
            rate=2.0,
        )
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_e, False, 10)
        transaction.complete()
        transaction.refresh_from_db()
        self.alan_acc_u1.refresh_from_db()
        self.alan_acc_e.refresh_from_db()
        self.assertEqual(transaction.status, PaymentTransaction.statuses.COMPLETED)
        self.assertEqual(self.alan_acc_u1.amount, 80)
        self.assertEqual(self.alan_acc_e.amount, 110)

    def test_complete_transaction_exchange_taxes(self):
        ExchangeRate.objects.create(
            source=Currency.objects.get(slug='USD'),
            destination=Currency.objects.get(slug='EUR'),
            rate=2.0,
        )
        transaction = PaymentTransaction.objects.request(self.alan_acc_u1, self.alan_acc_e, True, 10)
        transaction.complete()
        collect_taxes()
        transaction.refresh_from_db()
        self.alan_acc_u1.refresh_from_db()
        self.alan_acc_e.refresh_from_db()
        taxes_account = Account.objects.get(type=Account.types.TAXES_ACCOUNT, currency__slug='EUR')
        self.assertEqual(transaction.status, PaymentTransaction.statuses.COMPLETED)
        self.assertEqual(self.alan_acc_u1.amount, 78)
        self.assertEqual(self.alan_acc_e.amount, 110)
        self.assertEqual(taxes_account.amount, 1)

    def test_complete_transaction_long_exchange(self):
        ExchangeRate.objects.filter(source__slug='EUR', destination__slug='CNY').delete()
        ExchangeRate.objects.create(
            source=Currency.objects.get(slug='EUR'),
            destination=Currency.objects.get(slug='USD'),
            rate=2.0,
        )
        ExchangeRate.objects.create(
            source=Currency.objects.get(slug='USD'),
            destination=Currency.objects.get(slug='CNY'),
            rate=3.0,
        )
        transaction = PaymentTransaction.objects.request(self.alan_acc_e, self.alan_acc_c, False, 10)
        transaction.complete()
        transaction.refresh_from_db()
        self.alan_acc_e.refresh_from_db()
        self.alan_acc_c.refresh_from_db()
        self.assertEqual(transaction.status, PaymentTransaction.statuses.COMPLETED)
        self.assertEqual(self.alan_acc_e.amount, 40)
        self.assertEqual(self.alan_acc_c.amount, 110)
