from django.shortcuts import redirect, render
from zalo_crawler.zalo_fetcher import start_crawling

def dashboard_view(request):
    if request.method == "POST":
        start_crawling()
        return redirect('templates')
    return render(request, 'trangchu.html')