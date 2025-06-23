# movies/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser
from movies.models import Movie, Genre, Review, Watchlist, Actor, Person, MovieCredit

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_admin', 'is_blocked', 'is_active', 'date_joined')
    list_filter = ('is_admin', 'is_blocked')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('favorite_genre', 'bio', 'photo', 'is_admin', 'is_blocked')}),
    )
    actions = ['block_users', 'unblock_users']

    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)
        self.message_user(request, "Выбранные пользователи заблокированы.")
    block_users.short_description = "Заблокировать выбранных пользователей"

    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
        self.message_user(request, "Выбранные пользователи разблокированы.")
    unblock_users.short_description = "Разблокировать выбранных пользователей"

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'movie__title', 'review_text')
    actions = ['delete_reviews']

    def delete_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Удалено {count} отзывов.")
    delete_reviews.short_description = "Удалить выбранные отзывы"

# Регистрация моделей
admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Watchlist)
admin.site.register(Actor)
admin.site.register(Person)
admin.site.register(MovieCredit)