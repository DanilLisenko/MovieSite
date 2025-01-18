from django.urls import path
from . import views

app_name = 'users'  # Определяем пространство имен

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('saved/', views.saved_movies, name='saved_movies'),
    path('saved/add/', views.add_movie, name='add_movie'),
    path('watchlist/delete/<int:movie_id>/', views.delete_movie, name='delete_movie'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]

