from typing import List
from functools import lru_cache

from constance import config

from django.contrib.auth.models import User
from django.db import models, transaction

from payment_system.fields import MoneyField
from payment_system.managers import (
    CurrencyManager,
    ExchangeChainManager,
    PaymentTransactionManager,
    AccountManager
)
from payment_system import settings, constants


class Currency(models.Model):

    objects = CurrencyManager()

    slug = models.SlugField()
    description = models.TextField()


class ExchangeRate(models.Model):
    source = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='+')
    destination = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='+')
    rate = MoneyField()
    time = models.DateTimeField(db_index=True, auto_now_add=True)


    @classmethod
    def _get_actual_rate(cls, from_currency_id, to_currency_id):
        return (
            cls.objects.filter(source_id=from_currency, destination_id=to_currency)
            .order_by('-time')
            .first()
        )


    @classmethod
    def get_chain(cls, from_currency, to_currency):
        if from_currency == to_currency:
            return []
        rate = cls._get_actual_rate(from_currency.id, to_currency.id)
        if rate:
            return [rate]
        base_id = Currency.objects.base_currency_id()
        step1 = cls._get_actual_rate(from_currency.id, base_id)
        step2 = cls._get_actual_rate(base_id, to_currency.id)
        return [step1, step2]


class Account(models.Model):

    objects = AccountManager()

    types = constants.AccountType

    type = models.TextField(choices=types.CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='accounts')
    amount = MoneyField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='uniq_taxes_accounts',
                fields=['currency'],
                condition=models.Q(type=constants.AccountType.TAXES_ACCOUNT)
            ),
            models.CheckConstraint(
                name='user_account_with_user',
                check=(
                    models.Q(type=constants.AccountType.USER_ACCOUNT, user__isnull=False) |
                    models.Q(type=constants.AccountType.TAXES_ACCOUNT)
                )
            ),
        ]


class PaymentTransaction(models.Model):

    objects = PaymentTransactionManager()

    statuses = constants.PaymentTransactionStatus

    source = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='outgoing_transactions',
    )
    destination = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='incoming_transactions',
    )
    with_taxes = models.BooleanField(default=False)
    amount = MoneyField()
    # Denormalized field. Currency is always equal to source.currency
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='+')
    taxes = MoneyField(null=True)
    status = models.TextField(choices=statuses.CHOICES)

    def set_rate_and_taxes(self):
        chain = ExchangeRate.get_chain(self.source.currency_id, self.destination.currency_id)
        if chain:
            ExchangeChain.objects.from_exchange_sequence(self, chain)
        self.state = constants.PaymentTransactionStatus.RATE_CALCULATED
        if self.with_taxes:
            self.taxes = config.TAXES * self.amount

    def _lock(self):
        return (
            PaymentTransaction.objects
            .select_related('source', 'destination')
            .select_for_update()
            .get(id=self.id)
        )

    @transaction.atomic
    def complete(self):
        transaction = self._lock()
        if transaction.status == constants.PaymentTransactionStatus.COMPLETED:
            return
        if transaction.status == constants.PaymentTransactionStatus.SCHEDULED:
            transaction.set_rate_and_taxes()
        if transaction.source.amount < transaction.amount:
            transaction.status = constants.PaymentTransactionStatus.REJECTED
        else:
            transaction.source.amount -= transaction.amount
            if transaction.with_taxes:
                transaction.destination.amount += transaction.amount - transaction.taxes
                transaction.status = constants.PaymentTransactionStatus.USER_MONEY_TRANSMITTED
            else:
                transaction.destination.amount += transaction.amount
                transaction.status = constants.PaymentTransactionStatus.COMPLETED
        transaction.save()
        transaction.source.save(update_fields=['amount'])
        transaction.destination.save(update_fields=['amount'])


class ExchangeChain(models.Model):

    objects = ExchangeChainManager()

    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='exchange_chain'
    )
    exchange_rate = models.ForeignKey(
        ExchangeRate,
        on_delete=models.PROTECT,
        related_name='+'
    )
    order = models.IntegerField()
