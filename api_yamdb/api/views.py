from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title, User
from django.db.models import Avg

from .filters import TitleFilter
from api.permissions import (AdminModeratorAuthorPermission, AdminPermission,
                             IsAdminUserOrReadOnly)

from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, RegistrationSerializer,
                          ReviewSerializer, TitleSerializer,
                          UserSerializer,
                          VerificationSerializer)


class CreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass


from api.permissions import (AdminPermission, IsAdminUserOrReadOnly,
                             IsAuthorOrReadOnly, IsModeratorOrReadOnly)

from .filters import TitleFilter
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, RegistrationSerializer,
                          ReviewSerializer, TitleSerializer, UserSerializer,
                          VerificationSerializer)


class CreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass


class ModelMixinSet(CreateModelMixin, ListModelMixin,
                    DestroyModelMixin, GenericViewSet):
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    permission_classes = [AdminPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(
        detail=False,
        methods=['GET', 'PATCH'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True
            )
            if not (serializer.is_valid()):
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            if serializer.validated_data.get('role'):
                if request.user.role != 'admin' or not (
                    request.user.is_superuser
                ):
                    serializer.validated_data['role'] = request.user.role
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def registration_view(request):
    serializer = RegistrationSerializer(data=request.data)
    username = request.data.get('username')
    email = request.data.get('email')
    if not (serializer.is_valid()):
        try:
            User.objects.get(username=username, email=email)
        except ObjectDoesNotExist:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
    user, created = User.objects.get_or_create(username=username, email=email)
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        "YaMDb: код для подтверждения регистрации",
        f"Ваш код для получения токена: {confirmation_code}",
        "test@yamdb.com",
        [email],
        fail_silently=False,
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verification_view(request):
    serializer = VerificationSerializer(data=request.data)
    if not (serializer.is_valid()):
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    username = request.data.get('username')
    confirmation_code = request.data.get('confirmation_code')
    user = get_object_or_404(User, username=username)
    if not default_token_generator.check_token(user, confirmation_code):
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    token = AccessToken.for_user(user)
    return Response(data={'token': str(token)}, status=status.HTTP_200_OK)


class CategoryViewSet(ModelMixinSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter, )
    search_fields = ('name', )
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.select_related(
        'category').prefetch_related('genre').annotate(
        rating=Avg('reviews__score')).order_by('id')
    http_method_names = ['get', 'post', 'delete', 'patch']
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = PageNumberPagination
    serializer_class = TitleSerializer
    filterset_class = TitleFilter


class GenreViewSet(ModelMixinSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly | IsModeratorOrReadOnly | IsAdminUserOrReadOnly
    ]

    def get_review(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'))
        return review

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly  |  IsModeratorOrReadOnly | IsAdminUserOrReadOnly
    ]

    def get_title(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        return title

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())
