from typing import List
from functools import lru_cache

from constance import config

from django.contrib.auth.models import User
from django.db import models

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
    # WARNING
    rate = models.FloatField()
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
        on_delete=models.SET_NULL,
        null=True,
        related_name='outgoing_transactions',
    )
    destination = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        related_name='incoming_transactions',
    )
    amount = MoneyField()
    taxes = MoneyField(null=True)
    status = models.TextField(choices=statuses.CHOICES)


    def set_rate_and_taxes(self):
        chain = ExchangeRate.get_chain(self.source.currency_id, self.destination.currency_id)
        if chain:
            ExchangeChain.objects.from_exchange_sequence(self, chain)
        self.state = self.statuses.RATE_CALCULATED
        if self.taxes is None:
            self.taxes = config.TAXES * self.amount


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
