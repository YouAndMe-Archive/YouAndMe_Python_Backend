# import sqlite3

# conn = sqlite3.connect("database.db")
# print("데이터베이스 생성 성공!")

# conn.execute(
#     """
#     create table location (name text, addr1 text, addr2 text, latitude number, longitude number, phone number)
#     """
# )

# print("테이블 생성 성공!")

# conn.close()

import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# 테이블이 존재하는지 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='location';")
if cursor.fetchone() is None:
    # 테이블이 존재하지 않을 경우 생성
    cursor.execute(
        """
        create table location (name text, addr1 text, addr2 text, latitude number, longitude number, phone number)
        """
    )
    print("테이블 생성 성공!")
else:
    print("테이블이 이미 존재합니다.")

conn.commit()
conn.close()
