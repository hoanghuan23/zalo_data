# dashboard_view with crawling trigger
from django.shortcuts import redirect
from zalo_crawler.zalo_fetcher import start_crawling

def dashboard_view(request):
    if request.method == "POST":
        start_crawling()
        return redirect('dashboard')