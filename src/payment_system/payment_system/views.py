from django.contrib.auth.models import User
from django.db import transaction

from rest_framework import mixins, serializers, viewsets
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payment_system import models, serializers, tasks
from payment_system.responses import ErrorResponse



class CustomTokenAuthentication(BasicAuthentication):
    def authenticate(self, request):
        return request._request.user, None


class SignInView(APIView):
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def init_user(self, username, password):
        user = User.objects.create_user(username=username, password=password)
        models.Account.objects.create_init_user_set(user)

    def post(self, request):
        serializer = serializers.SignInSerializer(data=request.data)
        if not serializer.is_valid():
            return ErrorResponse(str(serializer.errors))
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        self.init_user(username, password)
        return Response({'result': 'ok'}, status=201)


class AccountsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = models.Account.objects.filter(user=request.user)
        serializer = serializers.AccountSerializer(accounts, many=True)
        return Response({
            'result': serializer.data
        })


class PaymentTransactionView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = serializers.PaymentTransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return ErrorResponse(str(serializer.errors))
        data = serializer.validated_data
        from_account = data['source']
        to_account = data['destination']
        if from_account.user != request.user:
            return ErrorResponse('You are not account\'s owner')
        transaction = models.PaymentTransaction.objects.request(
            from_account,
            to_account,
            from_account.user_id != to_account.user_id,
            data['amount'],
        )
        tasks.complete_transactions.apply_async(args=[transaction.id])
        return Response({'result': serializers.OutgoingTransactionSerializer(transaction).data})
