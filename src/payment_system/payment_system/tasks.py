from payment_system.models import PaymentTransaction
from payment_system.celery import app


@app.task
def complete_transactions():
    transactions = PaymentTransaction.objects.incompleted()
    for transaction in transactions:
        transaction.complete()
