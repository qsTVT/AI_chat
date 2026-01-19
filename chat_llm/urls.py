"""
URL configuration for chat_llm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from myapp import views

urlpatterns = [
    path("", views.home),
    path("admin/", admin.site.urls),
    path("face_collect/", views.face_collect),
    path("face_detect/", views.face_detect),
    path("face_enroll/", views.face_enroll),
    path("page/answer/", views.answer_page),
    path("page/login/", views.login_page),
    path("page/register/", views.register_page),
    path("page/admin/login/", views.admin_login_page),
    path("page/admin/dashboard/", views.admin_dashboard_page),
    path("api/admin/login/", views.api_admin_login),
    path("api/admin/search_user/", views.api_admin_search_user),
    path("api/admin/photo/<int:user_id>/", views.admin_photo),
    path("api/admin/check_password/", views.api_admin_check_password),
    path("api/admin/reset_password/", views.api_admin_reset_password),
    path("api/admin/delete_user/", views.api_admin_delete_user),
    path("page/stats/", views.stats_page),
    path("chat/", views.chat),
    path("session/", views.get_session),
    path("api/stats/age/", views.age_stats),
    path("api/login/", views.api_login),
    path("api/register/", views.api_register),
    path("api/logout/", views.api_logout),
    path("api/me/", views.api_me),
]
