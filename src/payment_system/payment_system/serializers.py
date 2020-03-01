from rest_framework import serializers

from payment_system import models, fields


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AccountSerializer(serializers.ModelSerializer):
    currency = serializers.CharField(source='currency.slug')
    description = serializers.CharField(source='currency.description')
    amount = serializers.CharField()
    class Meta:
        model = models.Account
        fields = ['currency', 'description', 'amount', 'id']


class ExchangeRateSerializer(serializers.ModelSerializer):
    
    source = serializers.CharField()
    destination = serializers.CharField()
    rate = serializers.CharField()
    time = serializers.DateTimeField()

    class Meta:
        model = models.ExchangeRate
        fields = ['source', 'destination', 'rate', 'time']


class PaymentTransactionSerializer(serializers.ModelSerializer):

    source = serializers.PrimaryKeyRelatedField(
        queryset=models.Account.objects.all(),
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=models.Account.objects.all(),
    )
    amount = fields.MoneySerializerField()

    class Meta:
        model = models.PaymentTransaction
        fields = ['source', 'destination', 'amount']


class OutgoingTransactionSerializer(PaymentTransactionSerializer):

    status = serializers.CharField(read_only=True)
    taxes = serializers.SerializerMethodField(read_only=True)
    exchange = serializers.SerializerMethodField(read_only=True)
    currency = serializers.CharField(source='currency.slug', read_only=True)

    class Meta:
        model = models.PaymentTransaction
        fields = ['source', 'destination', 'status', 'taxes', 'exchange', 'amount', 'currency']

    def get_taxes(self, instance):
        if instance.taxes:
            return f'{instance.taxes} {instance.currency.slug}'

    def get_exchange(self, instance):
        exchange_chain = list(instance.exchange_chain.all())
        # Sort objects in memory to decrease base requests count
        # All data prefetched before
        exchange_chain.sort(key=lambda item: item.order)
        return ExchangeRateSerializer(
            (item.exchange_rate for item in exchange_chain),
            many=True
        ).data
