from typing import List
from functools import lru_cache

from constance import config

from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone

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

    slug = models.SlugField(db_index=True, unique=True)
    description = models.TextField()


class ExchangeRate(models.Model):
    source = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='+')
    destination = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='+')
    rate = MoneyField()
    time = models.DateTimeField(db_index=True, auto_now_add=True)

    @classmethod
    def _get_actual_rate(cls, from_currency_id, to_currency_id):
        return (
            cls.objects.filter(source_id=from_currency_id, destination_id=to_currency_id)
            .order_by('-time')
            .first()
        )


    @classmethod
    def get_chain(cls, from_currency_id, to_currency_id):
        if from_currency_id == to_currency_id:
            return []
        rate = cls._get_actual_rate(from_currency_id, to_currency_id)
        if rate:
            return [rate]
        base_id = Currency.objects.base_currency_id()
        step1 = cls._get_actual_rate(from_currency_id, base_id)
        step2 = cls._get_actual_rate(base_id, to_currency_id)
        return [step1, step2]


class Account(models.Model):

    objects = AccountManager()

    types = constants.AccountType

    type = models.TextField(choices=types.CHOICES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, db_index=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='accounts', db_index=True)
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
            models.CheckConstraint(
                name='amount_gte_0',
                check=models.Q(amount__gte=0)
            ),
        ]


class PaymentTransaction(models.Model):

    objects = PaymentTransactionManager()

    statuses = constants.PaymentTransactionStatus

    source = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='outgoing_transactions',
        db_index=True,
    )
    destination = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='incoming_transactions',
        db_index=True,
    )
    with_taxes = models.BooleanField(default=False)
    amount = MoneyField()
    # Denormalized field. Currency is always equal to source.currency
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='+')
    taxes = MoneyField(default=0)
    status = models.TextField(choices=statuses.CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, db_index=True)
    spent = MoneyField(default=0)

    def set_rate_and_taxes(self):
        chain = ExchangeRate.get_chain(self.source.currency_id, self.destination.currency_id)
        if chain:
            ExchangeChain.objects.from_exchange_sequence(self, chain)
        self.state = constants.PaymentTransactionStatus.RATE_CALCULATED
        if self.with_taxes:
            self.taxes = config.TAXES * self.amount

    @classmethod
    def _lock(cls, transaction_id):
        return (
            PaymentTransaction.objects
            .select_related('source', 'destination')
            .select_for_update()
            .get(id=transaction_id)
        )

    def calculate_money_to_sub(self):
        result_money = self.amount + self.taxes
        rate_chain = (
            self.exchange_chain.order_by('-order')
            .select_related('exchange_rate')
            .values_list('exchange_rate__rate', flat=True)
        )
        for rate in rate_chain:
            result_money *= rate
        return result_money

    def _do_complete(self):
        if self.status in constants.PaymentTransactionStatus.FINISHED_STATUSES:
            return
        if self.status == constants.PaymentTransactionStatus.SCHEDULED:
            self.set_rate_and_taxes()
        money_to_sub = self.calculate_money_to_sub()
        if self.source.amount < money_to_sub:
            self.status = constants.PaymentTransactionStatus.REJECTED
        else:
            self.source.amount -= money_to_sub
            self.spent = money_to_sub
            self.destination.amount += self.amount
            if self.with_taxes:
                self.status = constants.PaymentTransactionStatus.USER_MONEY_TRANSMITTED
            else:
                self.status = constants.PaymentTransactionStatus.COMPLETED
        self.processed_at = timezone.now()
        self.save()
        self.source.save(update_fields=['amount'])
        self.destination.save(update_fields=['amount'])

    @classmethod
    @transaction.atomic
    def complete(cls, transaction_id):
        transaction = cls._lock(transaction_id)
        transaction._do_complete()



class ExchangeChain(models.Model):

    objects = ExchangeChainManager()

    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='exchange_chain',
        db_index=True,
    )
    exchange_rate = models.ForeignKey(
        ExchangeRate,
        on_delete=models.PROTECT,
        related_name='+',
        db_index=True,
    )
    order = models.IntegerField()
