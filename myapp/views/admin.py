import json
import os

import pymysql
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpResponse, JsonResponse

from .face import face_url
from .validators import validate_password_format


def api_admin_login(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 400, "msg": "请求数据格式错误"})
    username = data.get("username")
    password = data.get("password")
    if username == settings.MYAPP_ADMIN["USER"] and password == settings.MYAPP_ADMIN["PASSWORD"]:
        resp = JsonResponse({"code": 200, "msg": "登录成功", "redirect_url": "/page/admin/dashboard/"})
        resp.set_signed_cookie(
            key="admin_auth",
            value="1",
            salt="myapp_admin",
            httponly=True,
            samesite="Lax",
            secure=request.is_secure(),
        )
        return resp
    return JsonResponse({"code": 401, "msg": "管理员账号或密码错误"})


def api_admin_search_user(request):
    try:
        auth = request.get_signed_cookie("admin_auth", default=None, salt="myapp_admin")
    except Exception:
        auth = None
    if not auth:
        return JsonResponse({"code": 401, "msg": "未授权，请先登录管理员"})
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 400, "msg": "请求数据格式错误"})
    name = data.get("name")
    phone = data.get("phone")
    conn = None
    try:
        conn = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = conn.cursor()
        conditions = []
        params = []
        if name:
            conditions.append("user_name LIKE %s")
            params.append(f"%{name}%")
        if phone:
            conditions.append("phone = %s")
            params.append(phone)
        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT id, user_name, age, phone, password FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE {where}"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            uid = r[0]
            photo_path = os.path.join(face_url, f"{uid}.jpg")
            has_photo = os.path.isfile(photo_path)
            result.append({
                "id": uid,
                "name": r[1],
                "age": r[2],
                "phone": r[3],
                "password": r[4],
                "photo_url": f"/api/admin/photo/{uid}/" if has_photo else None,
            })
        return JsonResponse({"code": 200, "data": result})
    except Exception as e:
        print(e)
        return JsonResponse({"code": 500, "msg": "查询失败，请检查数据库连接与表结构"})
    finally:
        if conn:
            conn.close()


def admin_photo(request, user_id: int):
    try:
        auth = request.get_signed_cookie("admin_auth", default=None, salt="myapp_admin")
    except Exception:
        auth = None
    if not auth:
        return JsonResponse({"code": 401, "msg": "未授权，请先登录管理员"})
    path = os.path.join(face_url, f"{user_id}.jpg")
    if not os.path.isfile(path):
        return JsonResponse({"code": 404, "msg": "照片不存在"})
    with open(path, "rb") as f:
        data = f.read()
    return HttpResponse(data, content_type="image/jpeg")


def api_admin_check_password(request):
    try:
        auth = request.get_signed_cookie("admin_auth", default=None, salt="myapp_admin")
    except Exception:
        auth = None
    if not auth:
        return JsonResponse({"code": 401, "msg": "未授权，请先登录管理员"})
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 400, "msg": "请求数据格式错误"})
    user_id = data.get("user_id")
    pwd = data.get("password")
    if not user_id or not pwd:
        return JsonResponse({"code": 400, "msg": "用户ID与密码不能为空"})
    conn = None
    try:
        conn = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT password FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE id=%s", (user_id,))
        row = cursor.fetchone()
        if not row:
            return JsonResponse({"code": 404, "msg": "用户不存在"})
        hashed = row[0]
        ok = check_password(pwd, hashed)
        return JsonResponse({"code": 200, "data": {"valid": ok}})
    except Exception as e:
        print(e)
        return JsonResponse({"code": 500, "msg": "验证失败，请检查数据库连接"})
    finally:
        if conn:
            conn.close()


def api_admin_reset_password(request):
    try:
        auth = request.get_signed_cookie("admin_auth", default=None, salt="myapp_admin")
    except Exception:
        auth = None
    if not auth:
        return JsonResponse({"code": 401, "msg": "未授权，请先登录管理员"})
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 400, "msg": "请求数据格式错误"})
    user_id = data.get("user_id")
    new_password = data.get("new_password")
    if not user_id:
        return JsonResponse({"code": 400, "msg": "用户ID不能为空"})
    if not new_password:
        return JsonResponse({"code": 400, "msg": "新密码不能为空"})
    if not validate_password_format(new_password):
        return JsonResponse({"code": 400, "msg": "密码格式不正确"})
    hashed = make_password(new_password)
    conn = None
    try:
        conn = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {settings.MYAPP_DB['TABLE_USER_INFO']} SET password=%s WHERE id=%s",
            (hashed, user_id),
        )
        conn.commit()
        return JsonResponse({"code": 200, "msg": "修改成功"})
    except Exception as e:
        print(e)
        if conn:
            conn.rollback()
        return JsonResponse({"code": 500, "msg": "修改失败，请检查数据库连接与权限"})
    finally:
        if conn:
            conn.close()


def api_admin_delete_user(request):
    try:
        auth = request.get_signed_cookie("admin_auth", default=None, salt="myapp_admin")
    except Exception:
        auth = None
    if not auth:
        return JsonResponse({"code": 401, "msg": "未授权，请先登录管理员"})
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 400, "msg": "请求数据格式错误"})
    user_id = data.get("user_id")
    if not user_id:
        return JsonResponse({"code": 400, "msg": "用户ID不能为空"})

    conn = None
    try:
        conn = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE id=%s",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return JsonResponse({"code": 404, "msg": "用户不存在"})
        cursor.execute(
            f"DELETE FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE id=%s",
            (user_id,),
        )
        conn.commit()
    except Exception as e:
        print(e)
        if conn:
            conn.rollback()
        return JsonResponse({"code": 500, "msg": "删除失败，请检查数据库连接与权限"})
    finally:
        if conn:
            conn.close()

    deleted_files = []
    file_errors = []
    for ext in (".jpg", ".png"):
        path = os.path.join(face_url, f"{user_id}{ext}")
        if os.path.isfile(path):
            try:
                os.remove(path)
                deleted_files.append(path)
            except Exception as e:
                file_errors.append(str(e))

    if file_errors:
        return JsonResponse({
            "code": 200,
            "msg": "用户已删除，但照片删除失败",
            "data": {
                "deleted_files": deleted_files,
                "file_errors": file_errors,
            },
        })
    return JsonResponse({"code": 200, "msg": "删除成功"})
