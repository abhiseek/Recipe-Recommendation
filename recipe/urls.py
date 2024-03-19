from django.urls import path

from recipe import views

app_name = 'recipe'

urlpatterns = [
    path('', views.RecipeListAPIView.as_view(), name="recipe-list"),
    path('<int:pk>/', views.RecipeAPIView.as_view(), name="recipe-detail"),
    path('create/', views.RecipeCreateAPIView.as_view(), name="recipe-create"),
    path('<int:pk>/like/', views.RecipeLikeAPIView.as_view(), name='recipe-like'),
    path('<int:pk>/comment/', views.RecipeCommentAPIView.as_view(), name='recipe-comment'),
    path('comment/recipe/<int:pk>/', views.RecipeCommentAPIView.as_view(), name='recipe-comments'),
    path('my-recipes/', views.MyRecipeView.as_view(), name="view-user-recipe"),
    path('feed/', views.FeedAPIView.as_view(), name='feed'),

    path('yummly-autocomplete/', views.yummly_autocomplete, name='yummly_autocomplete'),
    path('yummly-search/', views.yummly_search, name='yummly_search'),
    path('yummly-feeds-list/', views.yummly_feeds_list, name='yummly_feeds_list'),
    path('get-categories-list/', views.get_categories_list, name='get_categories_list'),
    path('get-list-similarities/', views.get_list_similarities, name='get_list_similarities'),
    path('get-time-based-recipes/', views.time_based_yummly_feeds, name='get_time_based_feed'),
]
