import pymysql
from django.conf import settings
from django.http import JsonResponse


def age_stats(request):
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
        sql = f"SELECT user_name, age FROM {settings.MYAPP_DB['TABLE_USER_INFO']}"
        cursor.execute(sql)
        rows = cursor.fetchall()
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": 500,
            "msg": "统计数据查询失败，请稍后再试",
        })
    finally:
        if connection:
            connection.close()
    names = []
    ages = []
    buckets = {
        "0-18": 0,
        "19-30": 0,
        "31-40": 0,
        "41-60": 0,
        "60+": 0,
    }
    for row in rows:
        name = row[0]
        age_value = row[1]
        try:
            age = int(age_value)
        except (TypeError, ValueError):
            continue
        names.append(name)
        ages.append(age)
        if age <= 18:
            buckets["0-18"] += 1
        elif age <= 30:
            buckets["19-30"] += 1
        elif age <= 40:
            buckets["31-40"] += 1
        elif age <= 60:
            buckets["41-60"] += 1
        else:
            buckets["60+"] += 1
    pie_data = []
    for label, value in buckets.items():
        pie_data.append({
            "name": label,
            "value": value,
        })
    return JsonResponse({
        "code": 200,
        "msg": "成功",
        "data": {
            "pie": pie_data,
            "bar": {
                "names": names,
                "ages": ages,
            },
            "line": {
                "names": names,
                "ages": ages,
            },
        },
    })

