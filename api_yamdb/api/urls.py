from django.urls import path, include
from rest_framework import routers

from .views import Signup

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register('categories', CategoriesViewSet, basename='categories')
router_v1.register('genres', GenresViewSet, basename='genres')
router_v1.register("titles", TitleViewSet, basename = 'titles')
router_v1.register(
    r'^titles/(?P<titles_id>\d+)/comments', CommentViewSet, basename='comments'
)


urlpatterns = [
    path('v1/auth/signup/', Signup.as_view(), name='signup'),
    path('v1/auth/token/', Token.as_view(), name='token'),
    path('v1/', include(router_v1.urls)),
]
