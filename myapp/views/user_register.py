import json

from django.contrib.auth.hashers import make_password
from django.http import JsonResponse

from .face import face_insert, face_select, next_user_id
from .validators import validate_age, validate_password_format, validate_phone


def api_register(request):
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
    name = data.get("name")
    age = data.get("age")
    phone = data.get("phone")
    pwd = data.get("pwd")
    pwd2 = data.get("pwd2")
    if not name or not age or not phone or not pwd:
        return JsonResponse({
            "code": 400,
            "msg": "姓名、年龄、手机号和密码不能为空",
        })
    if not validate_age(age):
        return JsonResponse({
            "code": 400,
            "msg": "年龄必须是1-150岁的整数",
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
    if pwd2 is not None and pwd != pwd2:
        return JsonResponse({
            "code": 400,
            "msg": "两次输入的密码不一致",
        })
    try:
        existing = face_select(phone=phone)
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "数据库连接异常，请检查数据库配置或表是否存在",
        })
    if existing:
        return JsonResponse({
            "code": 400,
            "msg": "手机号已存在，不能重复注册",
        })
    user_id = next_user_id(1, 1999)
    if user_id is None:
        return JsonResponse({
            "code": 400,
            "msg": "注册人数已满，请联系管理员",
        })
    hashed_pwd = make_password(pwd)
    try:
        face_insert(user_id, name, age, phone, hashed_pwd)
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "注册失败，数据库异常，请检查表结构与权限",
        })
    resp = JsonResponse({
        "code": 200,
        "msg": "注册成功",
        "data": {
            "id": user_id,
            "name": name,
            "age": age,
            "phone": phone,
        },
    })
    resp.set_signed_cookie(
        key="user_auth",
        value=str(user_id),
        salt="myapp_user",
        httponly=True,
        samesite="Lax",
        secure=request.is_secure(),
    )
    return resp
