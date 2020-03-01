import re
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from payment_system.responses import ErrorResponse


class AuthenticationMiddleware(object):

    token_re = re.compile(r'^Token \w+$')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get('Authorization') or request.META.get('Authorization')
        if token and self.token_re.match(token):
            token = token.split(' ')[1]
            try:
                request.user = Token.objects.get(key=token).user
            except Token.DoesNotExist:
                pass
        return self.get_response(request)
