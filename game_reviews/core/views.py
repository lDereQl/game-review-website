from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def main_page(request):
    return render(request, 'core/main_page.html')
