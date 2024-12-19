from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages

class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.banned:
            logout(request)
            messages.error(request, "Your account has been banned. Contact support for more information.")
            return redirect('login')
        return self.get_response(request)
