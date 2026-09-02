"""
utils/database.py

- PostgreSQL(Supabase): Connection Pool 사용
- SQLite: 기존 연결 방식 유지
- 기존 SQLite 스타일 '?' 파라미터 문법 유지
- PostgreSQL에서는 내부적으로 '%s'로 변환
- row[0], row["column_name"] 방식 모두 지원
"""

import streamlit as st

from database.db import get_db_connection

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.pool import ThreadedConnectionPool

    PSYCOPG2_AVAILABLE = True

except ImportError:
    psycopg2 = None
    ThreadedConnectionPool = None
    PSYCOPG2_AVAILABLE = False


# =========================================================
# 1. PostgreSQL 사용 여부 확인
# =========================================================

def use_postgres() -> bool:
    """
    Streamlit Secrets에 DATABASE_URL이 있고
    psycopg2가 설치되어 있으면 PostgreSQL을 사용합니다.
    """
    if not PSYCOPG2_AVAILABLE:
        return False

    try:
        database_url = st.secrets.get("DATABASE_URL")
        return bool(database_url)

    except Exception:
        return False


# =========================================================
# 2. PostgreSQL Connection Pool
# =========================================================

@st.cache_resource
def get_postgres_pool():
    """
    Supabase PostgreSQL 연결 Pool을 앱 전체에서 하나만 생성합니다.

    Streamlit은 여러 사용자 세션을 여러 thread에서 처리할 수 있으므로
    ThreadedConnectionPool을 사용합니다.
    """
    if not use_postgres():
        return None

    return ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=st.secrets["DATABASE_URL"],
        connect_timeout=5
    )


# =========================================================
# 3. SQL 파라미터 변환
# =========================================================

def convert_query(query: str, is_pg: bool = True) -> str:
    """
    기존 SQLite 코드의 '?' placeholder를
    PostgreSQL psycopg2의 '%s' placeholder로 변환합니다.

    예:
        SELECT * FROM users WHERE student_id = ?

    ↓

        SELECT * FROM users WHERE student_id = %s
    """
    if is_pg:
        return query.replace("?", "%s")

    return query


# =========================================================
# 4. DB 연결 가져오기
# =========================================================

def _get_connection():
    """
    PostgreSQL:
        Connection Pool에서 기존 연결을 가져옵니다.

    SQLite:
        기존 get_db_connection() 사용
    """
    if use_postgres():
        pool = get_postgres_pool()
        conn = pool.getconn()

        # 연결이 비정상적으로 종료된 경우 새 연결 확보
        if conn.closed:
            pool.putconn(conn, close=True)
            conn = pool.getconn()

        return conn, True

    conn = get_db_connection()
    return conn, False


# =========================================================
# 5. DB 연결 반환
# =========================================================

def _release_connection(conn, is_pg: bool):
    """
    PostgreSQL:
        close하지 않고 Pool에 반환

    SQLite:
        실제 연결 종료
    """
    if conn is None:
        return

    if is_pg:
        pool = get_postgres_pool()

        try:
            # SELECT도 psycopg2에서는 transaction을 시작할 수 있으므로
            # Pool 반환 전에 transaction 상태 초기화
            if not conn.closed:
                conn.rollback()

            pool.putconn(conn)

        except Exception:
            # 비정상 connection은 Pool에서 제거
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass

    else:
        conn.close()


# =========================================================
# 6. 여러 행 조회
# =========================================================

def fetch_all(query: str, params: tuple = ()):
    """
    SELECT 결과 전체 반환

    PostgreSQL:
        DictCursor 사용

        row[0]
        row["student_id"]

        두 방식 모두 가능

    SQLite:
        기존 Row 설정을 그대로 사용
    """
    conn = None
    cur = None
    is_pg = False

    try:
        conn, is_pg = _get_connection()

        if is_pg:
            cur = conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor
            )
        else:
            cur = conn.cursor()

        sql = convert_query(query, is_pg)

        cur.execute(sql, params)

        return cur.fetchall()

    except Exception:
        if conn is not None and is_pg:
            try:
                conn.rollback()
            except Exception:
                pass

        raise

    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

        if conn is not None:
            _release_connection(conn, is_pg)


# =========================================================
# 7. 한 행 조회
# =========================================================

def fetch_one(query: str, params: tuple = ()):
    """
    SELECT 결과 한 행 반환

    결과가 없으면 None
    """
    conn = None
    cur = None
    is_pg = False

    try:
        conn, is_pg = _get_connection()

        if is_pg:
            cur = conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor
            )
        else:
            cur = conn.cursor()

        sql = convert_query(query, is_pg)

        cur.execute(sql, params)

        return cur.fetchone()

    except Exception:
        if conn is not None and is_pg:
            try:
                conn.rollback()
            except Exception:
                pass

        raise

    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

        if conn is not None:
            _release_connection(conn, is_pg)


# =========================================================
# 8. INSERT / UPDATE / DELETE
# =========================================================

def execute_query(query: str, params: tuple = ()):
    """
    INSERT / UPDATE / DELETE 실행

    성공:
        commit

    실패:
        rollback
    """
    conn = None
    cur = None
    is_pg = False

    try:
        conn, is_pg = _get_connection()

        cur = conn.cursor()

        sql = convert_query(query, is_pg)

        cur.execute(sql, params)

        conn.commit()

        # SQLite에서만 의미가 있음.
        # PostgreSQL은 RETURNING id를 사용하는 것이 정석입니다.
        if not is_pg:
            return getattr(cur, "lastrowid", None)

        return None

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass

        raise

    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

        if conn is not None:
            _release_connection(conn, is_pg)