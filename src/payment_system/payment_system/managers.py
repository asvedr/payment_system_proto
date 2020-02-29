from functools import lru_cache

from django.db import models, transaction

from payment_system import settings, constants


class CurrencyManager(models.Manager):

    @lru_cache(maxsize=1)
    def base_currency_id(self):
        self.filter(slug=settings.BASE_CURRENCY)


class ExchangeChainManager(models.Manager):

    def from_exchange_sequence(self, transaction, exchange_rate_sequence):
        steps = [
            self.model(
                transaction=transaction,
                order=order,
                exchange_rate=exchange_rate
            )
            for order, exchange_rate in enumerate(exchange_rate_sequence)
        ]
        self.bulk_create(steps)


class PaymentTransactionManager(models.Manager):

    @transaction.atomic
    def request(self, source, destination, with_taxes, amount):
        transaction = self.model(
            source=source,
            destination=destination,
            status=constants.PaymentTransactionStatus.SCHEDULED,
            amount=amount,
            taxes=None if with_taxes else 0,
        )
        if settings.IMMEDIATELY_RATE:
            transaction.set_rate_and_taxes()
        transaction.save()
        return transaction


class AccountManager(models.Manager):

    def create_missing_taxes_accounts(self):
        from payment_system.models import Currency

        currencies = Currency.objects.exclude(accounts__type=constants.AccountType.TAXES_ACCOUNT)
        accounts = [
            self.model(
                type=constants.AccountType.TAXES_ACCOUNT,
                currency=currency,
            )
            for currency in currencies
        ]
        self.bulk_create(accounts)
