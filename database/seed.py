import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import pandas as pd
from datetime import datetime, timedelta
from database.db import get_db_connection, init_db
from utils.date_utils import get_korea_now_str

DEPTS_CSV = os.path.join(BASE_DIR, "data", "departments.csv")
PRICES_CSV = os.path.join(BASE_DIR, "data", "prices.csv")

def seed_db():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Seed departments if empty
    cursor.execute("SELECT COUNT(*) FROM departments")
    dept_count = cursor.fetchone()[0]
    
    if dept_count == 0 and os.path.exists(DEPTS_CSV):
        df_depts = pd.read_csv(DEPTS_CSV)
        for _, row in df_depts.iterrows():
            dept_id = int(row['id'])
            code = str(row['code']).lower()
            qr_token = f"dept_{dept_id}_token_{code}_2026"
            cursor.execute(
                "INSERT INTO departments (id, name, code, description, current_price, qr_token) VALUES (?, ?, ?, ?, ?, ?)",
                (dept_id, row['name'], row['code'], row['description'], float(row['base_price']), qr_token)
            )
        conn.commit()
        print("✅ Departments seeded successfully with QR tokens.")
    else:
        # Ensure qr_tokens exist for departments if missing
        cursor.execute("SELECT id, code, qr_token FROM departments")
        dept_rows = cursor.fetchall()
        for d in dept_rows:
            if not d['qr_token']:
                qr_token = f"dept_{d['id']}_token_{str(d['code']).lower()}_2026"
                cursor.execute("UPDATE departments SET qr_token = ? WHERE id = ?", (qr_token, d['id']))
        conn.commit()

    # 2. Seed price_history if empty
    cursor.execute("SELECT COUNT(*) FROM price_history")
    price_count = cursor.fetchone()[0]
    
    if price_count == 0 and os.path.exists(PRICES_CSV):
        df_prices = pd.read_csv(PRICES_CSV)
        for _, row in df_prices.iterrows():
            cursor.execute(
                "INSERT INTO price_history (department_id, price, timestamp) VALUES (?, ?, ?)",
                (int(row['department_id']), float(row['price']), str(row['timestamp']))
            )
            # Update department's current_price to latest seeded price
            cursor.execute(
                "UPDATE departments SET current_price = ? WHERE id = ?",
                (float(row['price']), int(row['department_id']))
            )
        conn.commit()
        print("✅ Price history seeded successfully.")
    
    # 3. Seed news if empty
    cursor.execute("SELECT COUNT(*) FROM news")
    news_count = cursor.fetchone()[0]
    if news_count == 0:
        now_time = get_korea_now_str()
        sample_news = [
            (1, "🚀 컴퓨터공학과, 생성형 AI 해커톤 전국 1위 달성!", "학생들이 자체 개발한 LLM 모델이 최고상을 받으며 주가가 급등세를 타고 있습니다.", "BULLISH", now_time),
            (2, "⚡ 전자공학과, 차세대 3nm 반도체 신기술 발표", "반도체 연구실의 새로운 논문이 IEEE 저널에 수재되며 투자자들의 기대감이 고조되었습니다.", "BULLISH", now_time),
            (3, "🤖 기계공학과, 자율주행 모빌리티 경진대회 우승", "스마트 로보틱스 자율주행 차량이 만점을 기록하며 호재로 작용하고 있습니다.", "BULLISH", now_time),
            (10, "🛰️ 항공우주공학과, 초소형 위성 궤도 진입 성공", "자체 제작 위성이 성공적으로 통신에 성공하며 학과 가치가 급격히 올랐습니다.", "BULLISH", now_time),
            (4, "🧪 화학공학과, 차세대 2차전지 전고체 배터리 핵심 원천기술 확보", "친환경 에너지를 이끌 핵심 기술 발표로 기대감이 증폭되었습니다.", "BULLISH", now_time)
        ]
        for dept_id, title, content, impact, ts in sample_news:
            cursor.execute(
                "INSERT INTO news (department_id, title, content, impact, timestamp) VALUES (?, ?, ?, ?, ?)",
                (dept_id, title, content, impact, ts)
            )
        conn.commit()
        print("✅ Campus news seeded successfully.")

    # 4. Seed demo admin and demo user if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (student_id, name, coin) VALUES (?, ?, ?)",
            ("admin777", "admin777", 0.0)
        )
        cursor.execute(
            "INSERT INTO users (student_id, name, coin) VALUES (?, ?, ?)",
            ("202412345", "홍길동", 0.0)
        )
        conn.commit()
        print("✅ Initial users created.")
        
    conn.close()

if __name__ == "__main__":
    seed_db()
