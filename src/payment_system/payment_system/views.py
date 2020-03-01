from django.contrib.auth.models import User
from django.db import transaction

from rest_framework import mixins, serializers, viewsets
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payment_system import models, serializers
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
