from django.db import models

from payment_system.constants import PaymentTransactionStatus


class PaymentTransactionQuerySet(models.QuerySet):

    def incompleted(self):
        return self.exclude(status__in=PaymentTransactionStatus.FINISHED_STATUSES)

    def of_user(self, user):
        return self.filter(
            models.Q(source__account__user_id=user.id) |
            models.Q(destination__account__user_id=user.id)
        )