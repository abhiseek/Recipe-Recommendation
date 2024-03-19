from rest_framework import serializers

from .models import Recipe, RecipeCategory, RecipeLike, RecipeComment


class RecipeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeCategory
        fields = ('id', 'name')


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.SerializerMethodField()
    category_name = serializers.CharField(write_only=True)
    total_number_of_likes = serializers.SerializerMethodField()
    total_number_of_comments = serializers.SerializerMethodField()
    total_number_of_bookmarks = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'category', 'category_name', 'picture', 'title', 'desc',
                  'cook_time', 'ingredients', 'procedure', 'author', 'username',
                  'total_number_of_likes', 'total_number_of_comments','total_number_of_bookmarks')
        read_only_fields = ('category',)
    def get_username(self, obj):
        return obj.author.username

    def get_category_name(self, obj):
        return obj.category.name

    def get_total_number_of_likes(self, obj):
        return obj.get_total_number_of_likes()

    def get_total_number_of_comments(self, obj):
        return obj.get_total_number_of_comments()

    def get_total_number_of_bookmarks(self, obj):
        return obj.get_total_number_of_bookmarks()

    def create(self, validated_data):
        category_name = validated_data.pop('category_name')
        category, _ = RecipeCategory.objects.get_or_create(name=category_name)
        validated_data['category'] = category
        recipe = Recipe.objects.create(**validated_data)
        return recipe

    def update(self, instance, validated_data):
        print(validated_data)
        if 'category' in validated_data:
            nested_serializer = self.fields['category']
            nested_instance = instance.category
            nested_data = validated_data.pop('category')

            nested_serializer.update(nested_instance, nested_data)

        return super(RecipeSerializer, self).update(instance, validated_data)


class RecipeLikeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RecipeLike
        fields = ('id', 'user', 'recipe')


class RecipeCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeComment
        fields = ('id', 'user', 'recipe', 'text', 'created')
        read_only_fields = ['user', 'recipe']
