import pymysql
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from myapp.models import ChatMessage


def stats_dashboard(request):
    """
    聚合统计接口：返回年龄分布、性别分布、聊天趋势
    """
    # 1. 获取数据库连接
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
        
        # 2. 查询年龄和性别
        sql = f"SELECT user_name, age, gender FROM {settings.MYAPP_DB['TABLE_USER_INFO']}"
        cursor.execute(sql)
        rows = cursor.fetchall()
        
    except Exception as e:
        print(e)
        return JsonResponse({"code": 500, "msg": "查询用户数据失败"})
    finally:
        if connection:
            connection.close()

    # 3. 处理年龄分布
    age_buckets = {"0-18": 0, "19-30": 0, "31-40": 0, "41-60": 0, "60+": 0}
    # 4. 处理性别分布
    gender_buckets = {"男": 0, "女": 0, "未知": 0}

    for row in rows:
        # row: (name, age, gender)
        # 处理年龄
        try:
            age = int(row[1])
            if age <= 18: age_buckets["0-18"] += 1
            elif age <= 30: age_buckets["19-30"] += 1
            elif age <= 40: age_buckets["31-40"] += 1
            elif age <= 60: age_buckets["41-60"] += 1
            else: age_buckets["60+"] += 1
        except:
            pass
        
        # 处理性别
        g = row[2]
        if g in gender_buckets:
            gender_buckets[g] += 1
        else:
            gender_buckets["未知"] += 1

    age_pie = [{"name": k, "value": v} for k, v in age_buckets.items()]
    gender_pie = [{"name": k, "value": v} for k, v in gender_buckets.items()]

    # 5. 处理聊天趋势 (最近7天)
    try:
        seven_days_ago = timezone.now() - datetime.timedelta(days=6)
        daily_data = ChatMessage.objects.filter(created_at__gte=seven_days_ago)\
            .annotate(date=TruncDate('created_at'))\
            .values('date')\
            .annotate(count=Count('id'))\
            .order_by('date')
            
        dates = []
        counts = []
        data_map = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in daily_data if item['date']}
        
        for i in range(7):
            d = seven_days_ago + datetime.timedelta(days=i)
            d_str = d.strftime('%Y-%m-%d')
            dates.append(d_str)
            counts.append(data_map.get(d_str, 0))
    except Exception as e:
        print(f"Chat stats error: {e}")
        dates = []
        counts = []

    return JsonResponse({
        "code": 200,
        "msg": "成功",
        "data": {
            "age_pie": age_pie,
            "gender_pie": gender_pie,
            "trend": {
                "dates": dates,
                "counts": counts
            }
        }
    })


# 保留旧接口兼容性（如果前端还用的话，但我们会改前端）
def age_stats(request):
    return stats_dashboard(request)

