from rest_framework import serializers

from payment_system import models


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AccountSerializer(serializers.ModelSerializer):
    currency = serializers.CharField(source='currency.slug')
    description = serializers.CharField(source='currency.description')
    amount = serializers.CharField()
    class Meta:
        model = models.Account
        fields = ['currency', 'description', 'amount']
