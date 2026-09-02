"""
SQLite (engineering_stock.db) -> Supabase (PostgreSQL) 데이터 마이그레이션 스크립트
FK 관계를 고려한 순서로 데이터를 복사하고 행 수를 검증합니다.
"""

import os
import sys
import sqlite3
import psycopg2
import psycopg2.extras
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "engineering_stock.db")
SECRETS_PATH = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")

# FK 의존 관계를 고려한 테이블 순서
MIGRATION_TABLES = [
    "departments",
    "users",
    "department_checkins",
    "qr_checkins",
    "holdings",
    "transactions",
    "price_history",
    "price_schedule",
    "news"
]

# BIGSERIAL / SERIAL pk를 가진 테이블 목록 (시퀀스 동기화 필요)
SERIAL_TABLES = [
    "department_checkins",
    "qr_checkins",
    "transactions",
    "price_history",
    "price_schedule",
    "news"
]

def get_supabase_conn():
    if not os.path.exists(SECRETS_PATH):
        raise FileNotFoundError(f"secrets.toml 파일을 찾을 수 없습니다: {SECRETS_PATH}")
    
    secrets = toml.load(SECRETS_PATH)
    db_url = secrets.get("DATABASE_URL")
    if not db_url:
        raise ValueError("secrets.toml 파일에 'DATABASE_URL'이 정의되어 있지 않습니다.")
    
    conn = psycopg2.connect(db_url, sslmode="require")
    return conn

def get_sqlite_conn():
    if not os.path.exists(SQLITE_DB_PATH):
        raise FileNotFoundError(f"SQLite DB 파일을 찾을 수 없습니다: {SQLITE_DB_PATH}")
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate():
    print("=" * 65)
    print("🚀 SQLite -> Supabase (PostgreSQL) 데이터 마이그레이션 시작")
    print("=" * 65)

    sqlite_conn = get_sqlite_conn()
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = get_supabase_conn()
    pg_cur = pg_conn.cursor()

    try:
        # 1. Supabase 스키마가 초기화되어 있는지 확인 (schema_supabase.sql 실행)
        schema_path = os.path.join(BASE_DIR, "database", "schema_supabase.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            pg_cur.execute(schema_sql)
            pg_conn.commit()
            print("📋 [1/3] Supabase 스키마 검증 및 적용 완료")

        # 2. Supabase 기존 데이터 정리 (TRUNCATE CASCADE)
        print("🧹 [2/3] Supabase 기존 데이터 초기화 (TRUNCATE CASCADE)...")
        table_list_str = ", ".join(f'"{t}"' for t in reversed(MIGRATION_TABLES))
        pg_cur.execute(f"TRUNCATE TABLE {table_list_str} CASCADE;")
        pg_conn.commit()

        # 3. 테이블별 데이터 복사
        print("📦 [3/3] 테이블별 데이터 복사 중...")
        for table in MIGRATION_TABLES:
            # SQLite 컬럼 목록 조회
            sqlite_cur.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in sqlite_cur.fetchall()]
            cols_str = ", ".join(f'"{c}"' for c in columns)
            placeholders = ", ".join(["%s"] * len(columns))

            # SQLite 데이터 조회
            sqlite_cur.execute(f"SELECT {cols_str} FROM {table}")
            rows = sqlite_cur.fetchall()
            
            if rows:
                data = [tuple(r) for r in rows]
                insert_query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
                psycopg2.extras.execute_batch(pg_cur, insert_query, data)
                pg_conn.commit()
                print(f"  - {table:<22}: {len(rows):>5}행 복사 완료")
            else:
                print(f"  - {table:<22}:     0행 (데이터 없음)")

        # 4. PostgreSQL Sequence 동기화 (SERIAL/BIGSERIAL 컬럼 PK 충돌 방지)
        for table in SERIAL_TABLES:
            pg_cur.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 0) + 1,
                    false
                );
            """)
        pg_conn.commit()
        print("🔢 PostgreSQL Sequence (ID 자동 증가값) 동기화 완료")

        # 5. 행 수 비교 및 검증
        print("\n" + "=" * 65)
        print("🔍 [검증] SQLite vs Supabase 테이블별 행 수 (Row Count) 비교")
        print("=" * 65)
        print(f"{'테이블명':<24} | {'SQLite':>10} | {'Supabase':>10} | {'상태':>8}")
        print("-" * 65)

        all_match = True
        for table in MIGRATION_TABLES:
            sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_cnt = sqlite_cur.fetchone()[0]

            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
            pg_cnt = pg_cur.fetchone()[0]

            status = "✅ 일치" if sqlite_cnt == pg_cnt else "❌ 불일치"
            if sqlite_cnt != pg_cnt:
                all_match = False

            print(f"{table:<24} | {sqlite_cnt:>10} | {pg_cnt:>10} | {status:>8}")

        print("=" * 65)
        if all_match:
            print("🎉 모든 테이블의 데이터가 100% 완벽하게 마이그레이션되었습니다!")
        else:
            print("⚠️ 일부 테이블의 행 수가 일치하지 않습니다. 데이터를 확인해주세요.")
        print("=" * 65)

    except Exception as e:
        pg_conn.rollback()
        print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
        raise
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
