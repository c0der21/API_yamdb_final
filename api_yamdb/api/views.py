from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets, permissions
from rest_framework.decorators import action #api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken #AccessToken
from reviews.models import Category, Genre, Review, Title, User

from api.permissions import (
    AdminPermission,
    IsAdminUserOrReadOnly,
    AdminModeratorAuthorPermission,
)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer, SignupSerializer,
                          TitleReadSerializer, TitleWriteSerializer,
                          TokenSerializer, UserSerializer)


class CreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass


class ModelMixinSet(CreateModelMixin, ListModelMixin,
                    DestroyModelMixin, GenericViewSet):
    pass


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

    # @api_view(["POST"])
    # @permission_classes([permissions.AllowAny])
    # def registration_view(request):
    #     serializer = SignupSerializer(data=request.data)
    #     if not (serializer.is_valid()):
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     username = request.data.get("username")
    #     email = request.data.get("email")
    #     user, created = User.objects.get_or_create(username=username, email=email)
    #     confirmation_code = default_token_generator.make_token(user)
    #     send_mail(
    #         "YaMDb: код для подтверждения регистрации",
    #         f"Ваш код для получения токена: {confirmation_code}",
    #         "test@yamdb.com",
    #         [email],
    #         fail_silently=False,
    #     )
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    # @api_view(["POST"])
    # @permission_classes([permissions.AllowAny])
    # def verification_view(request):
    #     serializer = TokenSerializer(data=request.data)
    #     if not (serializer.is_valid()):
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     username = request.data.get("username")
    #     confirmation_code = request.data.get("confirmation_code")
    #     user = get_object_or_404(User, username=username)
    #     if not default_token_generator.check_token(user, confirmation_code):
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     token = AccessToken.for_user(user)
    #     return Response(data={"token": str(token)}, status=status.HTTP_200_OK)


class Token(APIView):
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_code = serializer.validated_data['confirmation_code']
        user = get_object_or_404(User, username=username)
        if user.confirmation_code != confirmation_code:
            return Response(
                'Неверный код подтверждения',
                status=status.HTTP_400_BAD_REQUEST
            )
        refresh = RefreshToken.for_user(user)
        token_data = {'token': str(refresh.access_token)}
        return Response(token_data, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "username"
    permission_classes = [permissions.IsAuthenticated, AdminPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username"]

    @action(
        detail=False,
        methods=["GET", "PATCH"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        if request.method == "PATCH":
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True
            )
            if not (serializer.is_valid()):
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            if serializer.validated_data.get("role"):
                if request.user.role != "admin" or not (
                    request.user.is_superuser
                ):
                    serializer.validated_data["role"] = request.user.role
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryViewSet(ModelMixinSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter, )
    search_fields = ('name', )
    lookup_field = 'slug'


class TitleViewSet(ModelViewSet):
    queryset = Title.objects.all()
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter, )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer

class GenreViewSet(ModelMixinSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name', )
    lookup_field = 'slug'


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AdminModeratorAuthorPermission,)
    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (AdminModeratorAuthorPermission,)
    
    def get_queryset(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)