import pymysql

# 데이터베이스 연결 설정
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='password',
    database='labor_policy',
    port=3307
)

try:
    with connection.cursor() as cursor:
        # 연결 테스트를 위한 간단한 쿼리
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"연결 성공: {result}")
finally:
    connection.close()