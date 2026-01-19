import json
import os

import cv2
try:
    import face_recognition
except ImportError:
    class MockFaceRecognition:
        def face_locations(self, *args, **kwargs): return []
        def face_encodings(self, *args, **kwargs): return []
        def load_image_file(self, *args, **kwargs): return None
        def face_distance(self, *args, **kwargs): return [1.0]
    face_recognition = MockFaceRecognition()
import pymysql
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import render

from myapp.util.ImageUtil import get_image_array

from .validators import validate_password_format


face_url = r"G:\zqzb\face"

FACE_DISTANCE_MATCH_THRESHOLD = 0.45
FACE_DISTANCE_DUPLICATE_THRESHOLD = 0.38
FACE_DISTANCE_MARGIN = 0.06


def _ensure_rgb(image_array):
    if image_array is None:
        return None
    if len(image_array.shape) == 2:
        return cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
    if image_array.shape[2] == 4:
        return cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
    return image_array


def _pick_largest_location(locations):
    top, right, bottom, left = max(locations, key=lambda l: (l[2] - l[0]) * (l[1] - l[3]))
    return (top, right, bottom, left)


def _get_single_face_encoding(rgb):
    locations = face_recognition.face_locations(rgb, model="hog")
    if not locations:
        return (None, None)
    if len(locations) != 1:
        return (None, None)
    loc = locations[0]
    encodings = face_recognition.face_encodings(rgb, [loc])
    if not encodings:
        return (None, None)
    return (encodings[0], loc)


def _iter_known_encodings():
    for filename in os.listdir(face_url):
        if not (filename.endswith(".jpg") or filename.endswith(".png")):
            continue
        try:
            file_id = int(filename.split(".")[0])
        except Exception:
            continue
        path = os.path.join(face_url, filename)
        try:
            img = face_recognition.load_image_file(path)
            locations = face_recognition.face_locations(img, model="hog")
            if not locations:
                continue
            loc = _pick_largest_location(locations)
            enc = face_recognition.face_encodings(img, [loc])
            if not enc:
                continue
            yield (file_id, enc[0])
        except Exception as e:
            print(e)
            continue


def _save_cropped_face(rgb, loc, dst_path):
    top, right, bottom, left = loc
    h, w = rgb.shape[0], rgb.shape[1]
    pad = int(0.25 * max(bottom - top, right - left))
    t = max(0, top - pad)
    b = min(h, bottom + pad)
    l = max(0, left - pad)
    r = min(w, right + pad)
    crop = rgb[t:b, l:r]
    if crop.size == 0:
        return False
    crop = cv2.resize(crop, (320, 320), interpolation=cv2.INTER_AREA)
    bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    return bool(cv2.imwrite(dst_path, bgr))


def _require_admin_or_user_password(phone, password):
    if not phone or not password:
        return (None, JsonResponse({"code": 400, "msg": "手机号和密码不能为空"}))
    try:
        user_info = face_select(phone=phone)
    except Exception as e:
        print(e)
        return (None, JsonResponse({"code": 500, "msg": "数据库连接异常，请稍后再试"}))
    if not user_info:
        return (None, JsonResponse({"code": 400, "msg": "用户不存在"}))
    hashed = user_info[4]
    if not check_password(password, hashed):
        return (None, JsonResponse({"code": 400, "msg": "用户名或密码错误"}))
    return (user_info, None)


def face_collect(request):
    if request.method == "GET":
        return render(request, "face_collect.html")
    if not os.path.isdir(face_url):
        try:
            os.makedirs(face_url, exist_ok=True)
        except Exception:
            return JsonResponse({
                "code": 500,
                "msg": "人脸存储目录不存在，且无法创建，请联系管理员",
            })
    data = json.loads(request.body.decode("utf-8"))
    name = data["name"]
    age = data["age"]
    phone = data["phone"]
    pwd = data["pwd"]
    pwd2 = data.get("pwd2")
    if not validate_password_format(pwd):
        return JsonResponse({
            "code": 500,
            "msg": "密码格式不正确",
        })
    if pwd2 is not None and pwd != pwd2:
        return JsonResponse({
            "code": 500,
            "msg": "两次输入的密码不一致",
        })
    try:
        user_info = face_select(phone=phone)
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "数据库连接异常，请稍后再试",
        })
    if user_info:
        return JsonResponse({
            "code": 500,
            "msg": "手机号已存在，不能重复注册",
        })
    image_array = get_image_array(request)
    rgb = _ensure_rgb(image_array)
    if rgb is None:
        return JsonResponse({
            "code": 500,
            "msg": "未检测到人脸",
        })
    current_encoding, loc = _get_single_face_encoding(rgb)
    if current_encoding is None:
        return JsonResponse({
            "code": 500,
            "msg": "未检测到人脸",
        })
    known_encodings = list(_iter_known_encodings())
    if known_encodings:
        distances = []
        for _, enc in known_encodings:
            try:
                distances.append(float(face_recognition.face_distance([enc], current_encoding)[0]))
            except Exception:
                continue
        if distances and min(distances) < FACE_DISTANCE_DUPLICATE_THRESHOLD:
            return JsonResponse({
                "code": 500,
                "msg": "已经录入过人脸信息",
            })
    name_id = next_user_id(1, 1999)
    if name_id is None:
        return JsonResponse({
            "code": 400,
            "msg": "注册人数已满，请联系管理员",
        })
    try:
        image_path = os.path.join(face_url, f"{name_id}.jpg")
        if not _save_cropped_face(rgb, loc, image_path):
            raise RuntimeError("write_failed")
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "保存人脸图片失败，请联系管理员",
        })
    hashed_pwd = make_password(pwd)
    try:
        face_insert(name_id, name, age, phone, hashed_pwd)
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "注册失败，数据库异常，请稍后再试",
        })
    resp = JsonResponse({
        "code": 200,
        "msg": "成功",
        "data": {
            "id": name_id,
            "name": name,
            "age": age,
            "phone": phone,
        },
    })
    resp.set_signed_cookie(
        key="user_auth",
        value=str(name_id),
        salt="myapp_user",
        httponly=True,
        samesite="Lax",
        secure=request.is_secure(),
    )
    return resp


def face_detect(request):
    if request.method == "GET":
        return render(request, "face_detect.html")
    if not os.path.isdir(face_url):
        return JsonResponse({
            "code": 500,
            "msg": "人脸库目录不存在，请联系管理员",
        })
    try:
        image_array = get_image_array(request)
        rgb = _ensure_rgb(image_array)
        if rgb is None:
            return JsonResponse({
                "code": 500,
                "msg": "未检测到人脸",
            })
        current_encoding, _ = _get_single_face_encoding(rgb)
        if current_encoding is None:
            return JsonResponse({
                "code": 500,
                "msg": "未检测到人脸",
            })
        best_id = None
        best_dist = None
        second_best = None
        for file_id, enc in _iter_known_encodings():
            try:
                dist = float(face_recognition.face_distance([enc], current_encoding)[0])
            except Exception:
                continue
            if best_dist is None or dist < best_dist:
                second_best = best_dist
                best_dist = dist
                best_id = file_id
            elif second_best is None or dist < second_best:
                second_best = dist
        accept = False
        if best_id is not None and best_dist is not None:
            if best_dist < FACE_DISTANCE_MATCH_THRESHOLD:
                if second_best is None:
                    accept = best_dist < (FACE_DISTANCE_MATCH_THRESHOLD - 0.05)
                else:
                    accept = (second_best - best_dist) >= FACE_DISTANCE_MARGIN
        if accept:
            file_id = best_id
            try:
                user_info = face_select(file_id)
            except Exception as e:
                print(e)
                return JsonResponse({
                    "code": 500,
                    "msg": "数据库连接异常，请稍后再试",
                })
            if user_info:
                resp = JsonResponse({
                    "code": 200,
                    "msg": f"匹配成功，当前用户是{user_info[1]}",
                    "data": {
                        "id": user_info[0],
                        "name": user_info[1],
                        "age": user_info[2],
                        "phone": user_info[3],
                    },
                    "redirect_url": "/page/answer/",
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
        return JsonResponse({
            "code": 500,
            "msg": "人脸匹配失败，未找到匹配的用户",
        })
    except Exception as e:
        print(f"人脸检测错误: {e}")
        return JsonResponse({
            "code": 500,
            "msg": "人脸检测过程发生异常，请稍后再试",
        })


def face_enroll(request):
    if request.method == "GET":
        return render(request, "face_enroll.html")
    if request.method != "POST":
        return JsonResponse({"code": 405, "msg": "只支持POST请求"})
    if not os.path.isdir(face_url):
        try:
            os.makedirs(face_url, exist_ok=True)
        except Exception:
            return JsonResponse({"code": 500, "msg": "人脸库目录不存在，请联系管理员"})
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"code": 400, "msg": "请求数据格式错误"})
    phone = data.get("phone")
    password = data.get("password")
    user_info, err = _require_admin_or_user_password(phone, password)
    if err:
        return err
    user_id = int(user_info[0])
    existing_path = os.path.join(face_url, f"{user_id}.jpg")
    if os.path.isfile(existing_path):
        return JsonResponse({"code": 400, "msg": "该账号已录入人脸，无需重复录入"})
    image_array = get_image_array(request)
    rgb = _ensure_rgb(image_array)
    if rgb is None:
        return JsonResponse({"code": 400, "msg": "未检测到人脸"})
    current_encoding, loc = _get_single_face_encoding(rgb)
    if current_encoding is None:
        return JsonResponse({"code": 400, "msg": "请确保画面中只有一张清晰人脸"})

    for other_id, enc in _iter_known_encodings():
        if other_id == user_id:
            continue
        try:
            dist = float(face_recognition.face_distance([enc], current_encoding)[0])
        except Exception:
            continue
        if dist < FACE_DISTANCE_DUPLICATE_THRESHOLD:
            return JsonResponse({"code": 400, "msg": "该人脸已被其他账号录入，无法重复录入"})

    tmp_path = os.path.join(face_url, f"{user_id}_tmp.jpg")
    try:
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)
    except Exception:
        pass
    try:
        if not _save_cropped_face(rgb, loc, tmp_path):
            raise RuntimeError("write_failed")
        os.replace(tmp_path, existing_path)
    except Exception as e:
        print(f"Error in face_enroll: {e}")
        try:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return JsonResponse({"code": 500, "msg": f"保存人脸图片失败: {str(e)}"})

    resp = JsonResponse({"code": 200, "msg": "录入成功", "data": {"id": user_id}})
    resp.set_signed_cookie(
        key="user_auth",
        value=str(user_id),
        salt="myapp_user",
        httponly=True,
        samesite="Lax",
        secure=request.is_secure(),
    )
    return resp


def face_select(id=None, phone=None):
    connection = None
    try:
        connection = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = connection.cursor()
        if id is not None:
            sql = f"SELECT * FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE id=%s"
            cursor.execute(sql, (id,))
            return cursor.fetchone()
        if phone is not None:
            sql = f"SELECT * FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE phone=%s"
            cursor.execute(sql, (phone,))
            return cursor.fetchone()
    finally:
        if connection:
            connection.close()


def face_insert(id, name, age, phone, pwd):
    db = None
    try:
        db = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = db.cursor()
        sql = f"insert into {settings.MYAPP_DB['TABLE_USER_INFO']}(id,user_name,age,phone,password) values(%s,%s,%s,%s,%s)"
        cursor.execute(sql, (id, name, age, phone, pwd))
        db.commit()
        print("插入成功")
        return True
    except Exception as e:
        print(e)
        if db:
            db.rollback()
        print("插入失败")
        raise
    finally:
        if db:
            db.close()


def next_user_id(min_id=1, max_id=1999):
    connection = None
    try:
        connection = pymysql.connect(
            host=settings.MYAPP_DB["HOST"],
            user=settings.MYAPP_DB["USER"],
            password=settings.MYAPP_DB["PASSWORD"],
            database=settings.MYAPP_DB["NAME"],
            charset=settings.MYAPP_DB["CHARSET"],
        )
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT MAX(id) FROM {settings.MYAPP_DB['TABLE_USER_INFO']} WHERE id BETWEEN %s AND %s",
            (min_id, max_id),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            nxt = int(row[0]) + 1
        else:
            nxt = min_id
        if nxt > max_id:
            return None
        return nxt
    finally:
        if connection:
            connection.close()
