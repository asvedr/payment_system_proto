from django.db import models

from payment_system.constants import PaymentTransactionStatus


class PaymentTransactionQuerySet(models.QuerySet):

    def incompleted(self):
        self.filter(status__in=[PaymentTransactionStatus.SCHEDULED, PaymentTransactionStatus.RATE_CALCULATED])
