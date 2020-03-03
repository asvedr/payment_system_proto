from celery.decorators import periodic_task

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from payment_system.models import PaymentTransaction, Account
from payment_system.celery import app


@periodic_task(run_every=timezone.timedelta(minutes=5))
def complete_transactions(transaction_id=None):
    if transaction_id:
        transactions = [transaction_id]
    else:
        transactions = (
            PaymentTransaction.objects
            .incompleted()
            .order_by('created_at')
            .values_list('id', flat=True)
        )
    for transaction_id in transactions:
        PaymentTransaction.complete(transaction_id)


@transaction.atomic
def collect_taxes_for_currency(account_id, currency):
    account = Account.objects.select_for_update().get(id=account_id)
    transactions_to_collect = PaymentTransaction.objects.filter(
        status=PaymentTransaction.statuses.USER_MONEY_TRANSMITTED,
        currency=currency,
    )
    taxes_sum = transactions_to_collect.aggregate(Sum('taxes'))['taxes__sum']
    if taxes_sum is not None:
        account.amount += taxes_sum
        account.save(update_fields=['amount'])
        transactions_to_collect.update(status=PaymentTransaction.statuses.COMPLETED)


@periodic_task(run_every=timezone.timedelta(minutes=5))
def collect_taxes():
    taxes_accounts = (
        Account.objects.filter(type=Account.types.TAXES_ACCOUNT)
        .values_list('id', 'currency')
    )
    for account_id, currency in taxes_accounts:
        collect_taxes_for_currency(account_id, currency)
