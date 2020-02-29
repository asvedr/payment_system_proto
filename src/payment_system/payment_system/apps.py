from django.apps import AppConfig


class PaymentSystemConfig(AppConfig):
    name = 'payment_system'
    verbose_name = 'Payment System'

    def ready(self):
        from payment_system import models
