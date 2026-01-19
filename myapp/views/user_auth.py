import json

from django.contrib.auth.hashers import check_password
from django.http import JsonResponse

from .face import face_select
from .validators import validate_password_format, validate_phone


def api_login(request):
    if request.method != "POST":
        return JsonResponse({
            "code": 405,
            "msg": "只支持POST请求",
        })
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({
            "code": 400,
            "msg": "请求数据格式错误",
        })
    phone = data.get("phone")
    pwd = data.get("password")
    if not phone or not pwd:
        return JsonResponse({
            "code": 400,
            "msg": "手机号和密码不能为空",
        })
    if not validate_phone(phone):
        return JsonResponse({
            "code": 400,
            "msg": "手机号必须为11位数字",
        })
    if not validate_password_format(pwd):
        return JsonResponse({
            "code": 400,
            "msg": "密码格式不正确",
        })
    try:
        user_info = face_select(phone=phone)
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "数据库连接异常，请稍后再试",
        })
    if user_info is None:
        return JsonResponse({
            "code": 400,
            "msg": "用户不存在",
        })
    if not check_password(pwd, user_info[4]):
        return JsonResponse({
            "code": 400,
            "msg": "用户名或密码错误",
        })
    resp = JsonResponse({
        "code": 200,
        "msg": "登录成功",
        "data": {
            "id": user_info[0],
            "name": user_info[1],
            "age": user_info[2],
            "phone": user_info[3],
        },
    })
    resp.set_signed_cookie(
        key="user_auth",
        value=str(user_info[0]),
        salt="myapp_user",
        httponly=True,
        samesite="Lax",
        secure=request.is_secure(),
    )
    return resp


def api_logout(request):
    resp = JsonResponse({"code": 200, "msg": "已退出登录"})
    resp.delete_cookie("user_auth", samesite="Lax")
    return resp


def api_me(request):
    try:
        user_id = request.get_signed_cookie("user_auth", default=None, salt="myapp_user")
    except Exception:
        user_id = None
    if not user_id:
        return JsonResponse({"code": 200, "data": None})
    try:
        info = face_select(id=int(user_id))
    except Exception as e:
        print(e)
        info = None
    if not info:
        return JsonResponse({"code": 200, "data": None})
    return JsonResponse({
        "code": 200,
        "data": {
            "id": info[0],
            "name": info[1],
            "age": info[2],
            "phone": info[3],
        },
    })

