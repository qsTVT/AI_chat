from .admin import (
    admin_photo,
    api_admin_check_password,
    api_admin_delete_user,
    api_admin_login,
    api_admin_reset_password,
    api_admin_search_user,
)
from .chat import chat, create_session, delete_session, get_messages, get_session, get_session_list, update_session_title
from .face import face_collect, face_detect, face_enroll, face_insert, face_select, next_user_id
from .pages import (
    admin_dashboard_page,
    admin_login_page,
    answer_page,
    home,
    login_page,
    register_page,
    stats_page,
)
from .stats import age_stats
from .user_auth import api_login, api_logout, api_me
from .user_register import api_register

__all__ = [
    "face_collect",
    "face_detect",
    "face_enroll",
    "face_select",
    "face_insert",
    "next_user_id",
    "home",
    "answer_page",
    "login_page",
    "register_page",
    "admin_login_page",
    "admin_dashboard_page",
    "stats_page",
    "api_admin_login",
    "api_admin_search_user",
    "admin_photo",
    "api_admin_check_password",
    "api_admin_reset_password",
    "api_admin_delete_user",
    "chat",
    "get_session",
    "create_session",
    "get_session_list",
    "get_messages",
    "delete_session",
    "update_session_title",
    "age_stats",
    "api_register",
    "api_login",
    "api_logout",
    "api_me",
]
