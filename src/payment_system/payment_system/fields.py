from django.db.models import DecimalField

from rest_framework import serializers

from payment_system import settings


class MoneyField(DecimalField):
    def __init__(self, **kwargs):
        kwargs['max_digits'] = settings.MONEY_MAX_DIGITS
        kwargs['decimal_places'] = settings.MONEY_DECIMAL_PLACES
        super().__init__(**kwargs)


class MoneySerializerField(serializers.DecimalField):
    def __init__(self, **kwargs):
        kwargs['max_digits'] = settings.MONEY_MAX_DIGITS
        kwargs['decimal_places'] = settings.MONEY_DECIMAL_PLACES
        super().__init__(**kwargs)
