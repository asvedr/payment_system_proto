from rest_framework import serializers, status
from rest_framework.response import Response


class ErrorResponse(Response):
    def __init__(self, message, status=status.HTTP_400_BAD_REQUEST):
        super().__init__({'message': message}, status=status)
