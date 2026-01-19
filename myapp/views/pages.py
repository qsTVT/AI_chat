from django.shortcuts import redirect, render


def home(request):
    return render(request, "home.html")


def answer_page(request):
    return render(request, "answer.html")


def login_page(request):
    return render(request, "login.html")


def register_page(request):
    return render(request, "register.html")


def admin_login_page(request):
    return render(request, "admin_login.html")


def admin_dashboard_page(request):
    try:
        auth = request.get_signed_cookie("admin_auth", default=None, salt="myapp_admin")
    except Exception:
        auth = None
    if not auth:
        return redirect("/page/admin/login/")
    return render(request, "admin_dashboard.html")


def stats_page(request):
    return render(request, "stats.html")

