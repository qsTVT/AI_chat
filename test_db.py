import os
import pymysql
import sys

# 模拟 settings 中的配置
MYAPP_DB = {
    "HOST": os.getenv("MYAPP_DB_HOST", "localhost"),
    "USER": os.getenv("MYAPP_DB_USER", "root"),
    "PASSWORD": os.getenv("MYAPP_DB_PASSWORD", "12345678"),
    "NAME": os.getenv("MYAPP_DB_NAME", "suse_face"),
    "CHARSET": os.getenv("MYAPP_DB_CHARSET", "utf8"),
}

print(f"Connecting to {MYAPP_DB['HOST']} as {MYAPP_DB['USER']}...")

try:
    connection = pymysql.connect(
        host=MYAPP_DB["HOST"],
        user=MYAPP_DB["USER"],
        password=MYAPP_DB["PASSWORD"],
        database=MYAPP_DB["NAME"],
        charset=MYAPP_DB["CHARSET"],
    )
    print("Connection successful!")
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    print("Database version:", cursor.fetchone())
    connection.close()
except Exception as e:
    print("Connection failed:", e)
