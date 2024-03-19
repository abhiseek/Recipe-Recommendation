from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import Recipe, RecipeLike, RecipeComment
from followers.models import Follower
from .serializers import RecipeLikeSerializer, RecipeSerializer, RecipeCommentSerializer
from .permissions import IsAuthorOrReadOnly
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import filters
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes
import requests
import datetime

headers = {
	"X-RapidAPI-Key": "a2902d5316msh18425308907ed14p12fb8cjsn00f739bb744d",
	"X-RapidAPI-Host": "yummly2.p.rapidapi.com"
}

class RecipeListAPIView(generics.ListAPIView):
    """
    Get: a collection of recipes
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (AllowAny,)
    filterset_fields = ('category__name', 'author__username')


class RecipeCreateAPIView(generics.CreateAPIView):
    """
    Create: a recipe
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, Update, Delete a recipe
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)


class RecipeLikeAPIView(generics.CreateAPIView):
    """
    Like, Dislike a recipe
    """
    serializer_class = RecipeLikeSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        new_like, created = RecipeLike.objects.get_or_create(
            user=request.user, recipe=recipe)
        if created:
            new_like.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        like = RecipeLike.objects.filter(user=request.user, recipe=recipe)
        if like.exists():
            like.delete()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeCommentAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = RecipeComment.objects.all()
    serializer_class = RecipeCommentSerializer

    def get_queryset(self):
        recipe_id = self.kwargs.get('pk')
        return RecipeComment.objects.filter(recipe_id=recipe_id)

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        new_like, created = RecipeComment.objects.get_or_create(
            user=request.user, recipe=recipe)
        if created:
            new_like.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CommentsonRecipesView(generics.ListCreateAPIView):
    queryset = RecipeComment.objects.all()
    serializer_class = RecipeCommentSerializer

    def get_queryset(self):
        queryset = RecipeComment.objects.all()
        recipe_id = self.kwargs.get('recipe_id')
        if recipe_id:
            queryset = queryset.filter(recipe__comment__id=comment_id)
        return queryset

class MyRecipeView(generics.ListCreateAPIView):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'category_name']

    def get_queryset(self):
        return Recipe.objects.filter(author=self.request.user)


class FeedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        following_users = Follower.objects.filter(from_user=request.user).values_list('to_user_id', flat=True)
        recipes = Recipe.objects.filter(author__in=following_users).order_by('-created_at')
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)


@extend_schema(
    description='Autocomplete API for Yummly',
    summary='Yummly Autocomplete',
    parameters=[
        OpenApiParameter(name='query', description='Query string for searching recipes', required=True, type=OpenApiTypes.STR)
    ],
    responses={
        200: inline_serializer(
            name='YummlyAutocompleteResponse',
            fields={
                'some_field': OpenApiTypes.STR,
                # Define the structure of your response here.
                # Replace 'some_field' and its type with the actual fields from your JSON response.
            }
        ),
        500: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
def yummly_autocomplete(request):
    query = request.GET.get('query', '')
    url = "https://yummly2.p.rapidapi.com/feeds/auto-complete"
    response = requests.get(url, headers=headers, params={"q": query})
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data from Yummly2 API"}, status=500)


@csrf_exempt
@extend_schema(
    description='Search API for Yummly',
    summary='Yummly Search',
    parameters=[
        OpenApiParameter(name='query', description='Search query', required=True, type=OpenApiTypes.STR),
        OpenApiParameter(name='start', description='Start index', required=False, type=OpenApiTypes.INT, default=0),
        OpenApiParameter(name='maxResults', description='Maximum number of results to return', required=False, type=OpenApiTypes.INT, default=3)
    ],
    responses={
        200: inline_serializer(
            name='YummlySearchResponse',
            fields={
                'some_field': OpenApiTypes.STR,
                # Define the structure of your response here
                # Replace 'some_field' and its type with the actual fields from your JSON response
            }
        ),
        500: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
def yummly_search(request):
    query = request.GET.get('query', '')
    start = request.GET.get('start', '0')
    maxResults = request.GET.get('maxResults', '3')
    url = "https://yummly2.p.rapidapi.com/feeds/search"
    params = {"q": query,"start": start,"maxResult": maxResults,}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data from Yummly2 API"}, status=response.status_code)

@csrf_exempt
@extend_schema(
    description='Fetch feeds list from Yummly based on tags',
    summary='Yummly Feeds List',
    parameters=[
        OpenApiParameter(name='start', description='Start index for fetching feeds', required=False, type=OpenApiTypes.INT, default=0),
        OpenApiParameter(name='limit', description='Number of feeds to fetch', required=False, type=OpenApiTypes.INT, default=1),
        OpenApiParameter(name='tag', description='Tag to filter feeds', required=False, type=OpenApiTypes.STR, default='')
    ],
    responses={
        200: inline_serializer(
            name='YummlyFeedsListResponse',
            fields={
                'some_field': OpenApiTypes.STR,
                # Define the structure of your response here
                # Replace 'some_field' and its type with the actual fields from your JSON response
            }
        ),
        500: OpenApiTypes.OBJECT
    }
)


def yummly_feeds_list(start, limit, tag=''):
    url = "https://yummly2.p.rapidapi.com/feeds/list"
    params = {"start": start, "limit": limit, "tag": tag }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data from Yummly2 API"}, status=response.status_code)

@csrf_exempt
@require_http_methods(["GET"])  # Only allow GET requests for this view
def get_list_similarities(request):
    url = "https://yummly2.p.rapidapi.com/feeds/list-similarities"
    params = request.GET.dict()
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data from the API"}, status=response.status_code)

@csrf_exempt
@extend_schema(
    description='Fetch categories list from Yummly',
    summary='Yummly Categories List',
    responses={
        200: inline_serializer(
            name='YummlyCategoriesListResponse',
            fields={
                'categories': OpenApiTypes.OBJECT,  # Adjust based on actual response structure
                # Define the structure of your response here
            }
        ),
        500: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
def get_categories_list(request):
    url = "https://yummly2.p.rapidapi.com/categories/list"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data from Yummly2 API"}, status=response.status_code)


@extend_schema(
    description='Fetch feeds list from Yummly based on the current time of day.',
    summary='Yummly Time-Based Feeds List',
    parameters=[
        OpenApiParameter(name='start', description='Start index for fetching feeds', required=False, type=OpenApiTypes.INT, default=0),
        OpenApiParameter(name='limit', description='Number of feeds to fetch', required=False, type=OpenApiTypes.INT, default=10),
    ],
    responses={
        200: {
"type": "object",

        },
        500: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
def time_based_yummly_feeds(request):
        now = datetime.datetime.now()
        hour = now.hour
        tag = ''

        if hour < 12:
            tag = 'list.recipe.search_based:fq:attribute_s_mv:course^course-Breakfast and Brunch'
        elif 12 <= hour < 15:
            tag = 'list.recipe.search_based:fq:attribute_s_mv:course^course-Lunch'
        elif 15 <= hour < 20:
            tag='list.recipe.search_based: fq:attribute_s_mv: (dish\\ ^ dish\\-cake)'
        elif 20 <= hour < 23:
            tag = 'list.recipe.search_based:fq:attribute_s_mv:(course^course-Main Dishes)'
        else:
            tag = 'list.recipe.search_based:fq:attribute_s_mv:course^course-Breakfast and Brunch'
        return yummly_feeds_list(0,5,tag)