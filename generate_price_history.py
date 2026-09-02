import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "engineering_stock.db"

# 같은 결과 재생성을 위해 seed 고정
random.seed(20260901)

START_TIME = datetime(2026, 9, 1, 0, 0, 0)
END_TIME = datetime(2026, 9, 2, 19, 0, 0)

MIN_PRICE = 50.0
MAX_PRICE = 99.0

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

try:
    # 1. 학과 조회
    departments = cur.execute("""
        SELECT id, name, current_price
        FROM departments
        ORDER BY id
    """).fetchall()

    print(f"✅ 학과 수: {len(departments)}")

    # 2. 기존 9/1 이후 가격 기록 삭제
    cur.execute("""
        DELETE FROM price_history
        WHERE timestamp >= ?
    """, (START_TIME.strftime("%Y-%m-%d %H:%M:%S"),))

    print(f"🗑️ 기존 9/1 이후 가격 기록 {cur.rowcount}건 삭제")

    total_generated = 0

    # 3. 학과별 가격 생성
    for dept in departments:
        dept_id = dept["id"]
        dept_name = dept["name"]

        # 9/1 시작가는 50~70 사이 랜덤
        price = round(random.uniform(50.0, 70.0), 1)
        start_price = price

        current_time = START_TIME
        generated = []

        while current_time <= END_TIME:

            # 시간당 -3% ~ +3%
            change_rate = random.uniform(-0.03, 0.03)

            price = price * (1 + change_rate)

            # 하한 50, 상한 99
            price = max(MIN_PRICE, min(MAX_PRICE, price))

            price = round(price, 1)

            generated.append(
                (
                    dept_id,
                    price,
                    current_time.strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            current_time += timedelta(hours=1)

        cur.executemany("""
            INSERT INTO price_history (
                department_id,
                price,
                timestamp
            )
            VALUES (?, ?, ?)
        """, generated)

        final_price = generated[-1][1]

        cur.execute("""
            UPDATE departments
            SET current_price = ?
            WHERE id = ?
        """, (final_price, dept_id))

        total_generated += len(generated)

        print(
            f"{dept_id}. {dept_name}"
            f" | 시작 {start_price:.1f}"
            f" → 현재 {final_price:.1f}"
            f" | {len(generated)}건"
        )

    conn.commit()

    print("")
    print("======================================")
    print("✅ 9/1 이후 주가 데이터 생성 완료")
    print(f"✅ 총 생성 건수: {total_generated}")
    print("✅ 가격 하한: 50.0")
    print("✅ 가격 상한: 99.0")
    print("======================================")

except Exception as e:
    conn.rollback()
    print(f"❌ 생성 실패: {e}")
    raise

finally:
    conn.close()