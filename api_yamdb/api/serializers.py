from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')

    def validate_username(self, username):
        if username.lower() == "me":
            raise serializers.ValidationError(
                'Использовать имя "me" запрещено!'
            )
        return username


class VerificationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=250)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")
        lookup_field = "slug"


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("name", "slug")
        lookup_field = "slug"


class CategoryField(serializers.SlugRelatedField):
    def to_representation(self, value):
        serializer = CategorySerializer(value)
        return serializer.data


class GenreField(serializers.SlugRelatedField):
    def to_representation(self, value):
        serializer = GenreSerializer(value)
        return serializer.data


class TitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field="slug")
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field="slug", many=True)
    rating = serializers.IntegerField(required=False)

    class Meta:
        fields = (
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category'
        )
        model = Title
        
    def to_representation(self, instance):
        representation  = super().to_representation(instance)
        representation ["category"] = CategorySerializer(instance.category).data
        representation ["genre"] = GenreSerializer(instance.genre, many=True).data
        return representation


class ReviewSerializer(serializers.ModelSerializer):

    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username', many=False
    )

    def validate(self, attrs):
        author = (self.context["request"].user.id,)
        title = self.context["view"].kwargs.get("title_id")
        message = "Author review already exist"
        if (
            not self.instance
            and Review.objects.filter(title=title, author=author).exists()
        ):
            raise serializers.ValidationError(message)
        return attrs

    class Meta:
        model = Review
        fields = ['id', 'text', 'author', 'score', 'pub_date']


class TokenSerializer(serializers.Serializer):
    """Класс для преобразования данных при получении токена."""
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)
