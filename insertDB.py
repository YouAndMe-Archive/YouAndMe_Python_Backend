import sqlite3
import pandas as pd

# CSV 파일 경로
csv_file_path = "./data.csv"

# 데이터베이스 연결
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# location 테이블이 존재하는지 확인하고 생성
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    addr1 TEXT,
    addr2 TEXT,
    latitude REAL,
    longitude REAL,
    phone TEXT
)
"""
)

try:
    # CSV 파일 읽기
    df = pd.read_csv(csv_file_path, encoding="cp949")

    # 컬럼 이름 수정
    df.columns = df.columns.str.strip()

    # 데이터프레임의 각 행을 location 테이블에 삽입
    for row in df.itertuples(index=False):
        cursor.execute(
            """
            INSERT INTO location (name, addr1, addr2, latitude, longitude, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row.대상시설명,
                row.소재지도로명주소,
                row.소재지지번주소,
                row.위도,
                row.경도,
                row.관리기관전화번호,
            ),
        )

    # 커밋
    conn.commit()
    print("CSV 파일의 데이터를 데이터베이스에 성공적으로 삽입했습니다!")

except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {csv_file_path}")
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    # 연결 종료
    conn.close()
