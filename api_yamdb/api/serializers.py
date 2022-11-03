from rest_framework import serializers

from reviews.models import


class SignupSerializer(serializers.Serializer):
    """Класс для преобразования данных при получении кода подтверждения."""
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)


class TokenSerializer(serializers.Serializer):
    """Класс для преобразования данных при получении токена."""
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)
