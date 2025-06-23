from django.shortcuts import redirect
from django.urls import reverse

class BlockUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and (request.user.is_blocked or not request.user.is_active):
            # Разрешаем доступ к страницам логина и логаута
            if request.path not in [reverse('users:login'), reverse('logout')]:
                return redirect('users:login')
        response = self.get_response(request)
        return response