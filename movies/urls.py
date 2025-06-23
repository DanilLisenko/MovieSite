# movies/urls.py
from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('search/', views.search, name='search'),
    path('search/actors/', views.search_actors, name='search_actors'),
    path('search-page/', views.search_page, name='search_page'),
    path('recommend/', views.recommend_movie, name='recommend_movie'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:movie_id>/actors/', views.load_more_actors, name='load_more_movie_actors'),
    path('person/<int:person_id>/', views.person_detail, name='person_detail'),
    path('movie/<int:movie_id>/add-to-watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('movie/<int:movie_id>/mark-as-watched/', views.mark_as_watched, name='mark_as_watched'),
    path('collections/', views.movie_collections, name='movie_collections'),
    path('collections/<str:collection_type>/', views.collection_detail, name='collection_detail'),
    path('actor/<int:actor_id>/', views.actor_detail, name='actor_detail'),
    path('actors/', views.actors_list, name='actors_list'),
    path('actors/load-more/', views.load_more_actors, name='load_more_actors'),
    path('actor/<int:actor_id>/toggle-favorite/', views.toggle_favorite_actor, name='toggle_favorite_actor'),
    path('movie/actors/load-more/', views.load_more_movie_actors, name='load_more_movie_actors'),
    path('upcoming/', views.upcoming_movies_view, name='upcoming_movies'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('admin/unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('admin/delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('review/<int:review_id>/delete_own/', views.delete_own_review, name='delete_own_review'),
]