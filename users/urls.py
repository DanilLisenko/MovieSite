from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('user/<int:user_id>/block/', views.block_user, name='block_user'),
    path('watchlist/delete/<int:movie_id>/', views.delete_movie, name='delete_movie'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]