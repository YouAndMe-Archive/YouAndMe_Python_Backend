FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 현재 디렉토리의 모든 파일을 /app으로 복사
COPY . .

# pip 업데이트 및 requirements.txt 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 데이터베이스 생성 및 삽입 스크립트 실행
RUN python3 createDB.py
RUN python3 insertDB.py

# Flask 실행
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
