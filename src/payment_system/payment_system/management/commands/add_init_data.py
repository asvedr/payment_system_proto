from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from payment_system.models import Currency, Account, ExchangeRate
from payment_system import constants


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        ExchangeRate.objects.all().delete()
        Account.objects.all().delete()
        Currency.objects.all().delete()
        User.objects.all().delete()

        User.objects.create_user(
            username='john',
            email='johnwick@continental.com',
            password='dog',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        usd = Currency.objects.create(slug='USD', description='USA United States Dollar')
        eur = Currency.objects.create(slug='EUR', description='European Euro')
        cny = Currency.objects.create(slug='CNY', description='Chinese Yuán')
        rub = Currency.objects.create(slug='RUB', description='Russian Ruble')
        ExchangeRate.objects.bulk_create([
            ExchangeRate(
                source=usd,
                destination=eur,
                rate=0.91,
            ),
            ExchangeRate(
                source=eur,
                destination=usd,
                rate=1.1,
            ),
            ExchangeRate(
                source=usd,
                destination=cny,
                rate=6.99,
            ),
            ExchangeRate(
                source=cny,
                destination=usd,
                rate=0.14,
            ),
            ExchangeRate(
                source=usd,
                destination=rub,
                rate=66.99,
            ),
            ExchangeRate(
                source=rub,
                destination=usd,
                rate=0.015,
            ),
            ExchangeRate(
                source=eur,
                destination=cny,
                rate=7.67,
            ),
            ExchangeRate(
                source=cny,
                destination=eur,
                rate=0.13,
            ),
        ])
        Account.objects.create_missing_taxes_accounts()
