from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from reviews.models import Category, Genre, Review, Title, User

from .permissions import (ReadOnlyPermission, UserIsAuthor, AdminPermission, ModeratorPermission)
from .serializers import (SignupSerializer, TokenSerializer)

class Signup(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        try:
            user, _ = User.objects.get_or_create(
                email=email,
                username=username,
            )
        except IntegrityError:
            return Response(
                (
                    'Проблема в аутентификации:'
                    'Пользователь с таким username или email уже используется.'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            'Вы зарегистрировались на ресурсе.',
            f'Ваш код-подтверждение: {confirmation_code}',
            settings.DEFAULT_FROM_EMAIL,
            (email,),
            fail_silently=False,
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)