-- ==============================================================================
-- KUSPI (건국대학교 공과대학 학과 모의 주식 거래소) PostgreSQL / Supabase Schema
-- ==============================================================================

-- 1. users 테이블
CREATE TABLE IF NOT EXISTS users (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    coin DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. departments 테이블
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT,
    description TEXT,
    current_price DOUBLE PRECISION NOT NULL,
    qr_token TEXT UNIQUE
);

-- 3. department_checkins 테이블 (학과 부스 QR 체크인)
CREATE TABLE IF NOT EXISTS department_checkins (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT DEFAULT '2026_EXPO',
    student_id TEXT NOT NULL REFERENCES users(student_id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    reward_coin DOUBLE PRECISION DEFAULT 100.0,
    checked_in_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    qr_token_id TEXT,
    UNIQUE(event_id, student_id, department_id)
);

-- 4. qr_checkins 테이블 (전체 14개 QR 체크인)
CREATE TABLE IF NOT EXISTS qr_checkins (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES users(student_id) ON DELETE CASCADE,
    qr_event_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    reward_coin DOUBLE PRECISION DEFAULT 100.0,
    checked_in_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, qr_event_id)
);

-- 5. holdings 테이블 (학생별 학과 주식 보유 현황)
CREATE TABLE IF NOT EXISTS holdings (
    student_id TEXT NOT NULL REFERENCES users(student_id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    average_price DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    PRIMARY KEY (student_id, department_id)
);

-- 6. transactions 테이블 (매수/매도 거래 내역)
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES users(student_id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    quantity INTEGER NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. price_history 테이블 (주가 변동 기록)
CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    price DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. price_schedule 테이블 (예약된 주가 변동 스케줄)
CREATE TABLE IF NOT EXISTS price_schedule (
    id BIGSERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    is_applied INTEGER DEFAULT 0
);

-- 9. news 테이블 (공과대학 호재/악재 뉴스 및 공시)
CREATE TABLE IF NOT EXISTS news (
    id BIGSERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    impact TEXT DEFAULT 'NEUTRAL',
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 성능 최적화 인덱스
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_price_history_dept_ts ON price_history(department_id, timestamp DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_student ON transactions(student_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_dept ON transactions(department_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_qr_checkins_student ON qr_checkins(student_id);
CREATE INDEX IF NOT EXISTS idx_dept_checkins_student ON department_checkins(student_id);
CREATE INDEX IF NOT EXISTS idx_holdings_student ON holdings(student_id);
CREATE INDEX IF NOT EXISTS idx_news_dept ON news(department_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news(timestamp DESC);
