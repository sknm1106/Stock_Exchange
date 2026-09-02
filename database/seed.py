import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import pandas as pd
from datetime import datetime, timedelta
from database.db import init_db
from utils.database import fetch_all, fetch_one, execute_query
from utils.date_utils import get_korea_now_str

DEPTS_CSV = os.path.join(BASE_DIR, "data", "departments.csv")

def seed_db():
    init_db()
    
    # 1. Seed departments if count != 9
    dept_count_row = fetch_one("SELECT COUNT(*) FROM departments")
    dept_count = dept_count_row[0] if dept_count_row else 0
    
    if dept_count != 9 and os.path.exists(DEPTS_CSV):
        execute_query("DELETE FROM news")
        execute_query("DELETE FROM price_history")
        execute_query("DELETE FROM departments")
        
        df_depts = pd.read_csv(DEPTS_CSV)
        for _, row in df_depts.iterrows():
            dept_id = int(row['id'])
            code = str(row['code']).lower()
            qr_token = f"dept_{dept_id}_token_{code}_2026"
            execute_query(
                "INSERT INTO departments (id, name, code, description, current_price, qr_token) VALUES (?, ?, ?, ?, ?, ?)",
                (dept_id, row['name'], row['code'], row['description'], float(row['base_price']), qr_token)
            )
        print("✅ 9 Departments seeded successfully with QR tokens.")
    else:
        # Ensure qr_tokens exist for departments if missing
        dept_rows = fetch_all("SELECT id, code, qr_token FROM departments")
        for d in dept_rows:
            if not d['qr_token']:
                qr_token = f"dept_{d['id']}_token_{str(d['code']).lower()}_2026"
                execute_query("UPDATE departments SET qr_token = ? WHERE id = ?", (qr_token, d['id']))

    # 2. Seed initial price_history if empty
    INITIAL_PRICES = {
        1: 65.0,  # 사회환경공학부
        2: 74.0,  # 기계·로봇·자동차공학부
        3: 72.0,  # 전기전자공학부
        4: 71.0,  # 화공·생명·에너지공학부
        5: 66.0,  # 컴퓨터공학부
        6: 65.0,  # 재료공학과
        7: 67.0,  # 항공우주·모빌리티공학과
        8: 68.0,  # 생물공학과
        9: 74.0,  # 산업공학과
    }

    price_count_row = fetch_one("SELECT COUNT(*) FROM price_history")
    price_count = price_count_row[0] if price_count_row else 0

    if price_count == 0:
        now_time = get_korea_now_str()
        dept_rows = fetch_all("SELECT id FROM departments ORDER BY id ASC")

        for dept in dept_rows:
            dept_id = int(dept["id"])
            initial_price = INITIAL_PRICES.get(dept_id, 70.0)

            # departments 현재가와 차트 시작 가격을 반드시 동일하게 맞춤
            execute_query(
                "UPDATE departments SET current_price = ? WHERE id = ?",
                (initial_price, dept_id)
            )

            # 학과별 시작 가격은 딱 1건만 기록
            execute_query(
                """
                INSERT INTO price_history
                    (department_id, price, timestamp)
                VALUES (?, ?, ?)
                """,
                (dept_id, initial_price, now_time)
            )

        print("✅ Initial prices seeded: 9 departments / 60~80 Coin")
    
    # 3. Seed news if empty
    news_count_row = fetch_one("SELECT COUNT(*) FROM news")
    news_count = news_count_row[0] if news_count_row else 0
    if news_count == 0:
        sample_news = [
            (5, "🚀 컴퓨터공학부, 생성형 AI 해커톤 전국 1위 달성!", "학생들이 자체 개발한 LLM 모델이 최고상을 받으며 주가가 급등세를 타고 있습니다.", "BULLISH", "2026-08-11 09:30:00"),
            (3, "⚡ 전기전자공학부, 차세대 3nm 반도체 신기술 발표", "반도체 연구실의 새로운 논문이 IEEE 저널에 수재되며 투자자들의 기대감이 고조되었습니다.", "BULLISH", "2026-08-11 10:15:00"),
            (2, "🤖 기계·로봇·자동차공학부, 자율주행 모빌리티 경진대회 우승", "스마트 로보틱스 자율주행 차량이 만점을 기록하며 호재로 작용하고 있습니다.", "BULLISH", "2026-08-11 11:00:00"),
            (7, "🛰️ 항공우주·모빌리티공학과, 초소형 위성 궤도 진입 성공", "자체 제작 위성이 성공적으로 통신에 성공하며 학과 가치가 급격히 올랐습니다.", "BULLISH", "2026-08-11 11:45:00"),
            (4, "🧪 화공·생명·에너지공학부, 차세대 2차전지 전고체 배터리 핵심 원천기술 확보", "친환경 에너지를 이끌 핵심 기술 발표로 기대감이 증폭되었습니다.", "BULLISH", "2026-08-11 12:30:00")
        ]
        for dept_id, title, content, impact, ts in sample_news:
            execute_query(
                "INSERT INTO news (department_id, title, content, impact, timestamp) VALUES (?, ?, ?, ?, ?)",
                (dept_id, title, content, impact, ts)
            )
        print("✅ Campus news seeded successfully.")

    # 4. Seed demo admin and demo user if empty
    users_count_row = fetch_one("SELECT COUNT(*) FROM users")
    if users_count_row and users_count_row[0] == 0:
        execute_query(
            "INSERT INTO users (student_id, name, coin) VALUES (?, ?, ?)",
            ("admin1463", "admin1463", 0.0)
        )
        execute_query(
            "INSERT INTO users (student_id, name, coin) VALUES (?, ?, ?)",
            ("202412345", "홍길동", 0.0)
        )
        print("✅ Initial users created.")

if __name__ == "__main__":
    seed_db()

