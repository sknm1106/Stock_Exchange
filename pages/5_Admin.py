import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import pandas as pd
from utils.ui import apply_custom_theme
from utils.database import fetch_all, fetch_one, execute_query
from utils.trade import get_departments_list, get_all_transactions
from utils.auth import get_all_users, update_user_coin, get_user
from scheduler.scheduler import update_prices_now
from database.seed import seed_db

st.set_page_config(
    page_title="관리자 페이지 | Engineering Stock Exchange",
    page_icon="⚙️",
    layout="wide"
)

apply_custom_theme()

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
    <div>
        <h2 style="margin:0; font-weight: 800; color: #F8FAFC;">⚙️ Admin Control Center</h2>
        <div style="color: #94A3B8; font-size: 0.9rem;">행사 운영진 및 시스템 관리자 전용 메뉴</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Admin Auth check
if 'admin_authenticated' not in st.session_state:
    st.session_state['admin_authenticated'] = False

if not st.session_state['admin_authenticated']:
    col_a1, col_a2, col_a3 = st.columns([1, 2, 1])
    with col_a2:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <h3>🔐 관리자 인증</h3>
            <p style="color: #94A3B8; font-size: 0.9rem;">관리자 암호를 입력하여 로그인해주세요. (기본: admin123)</p>
        </div>
        """, unsafe_allow_html=True)
        
        admin_pass = st.text_input("관리자 비밀번호", type="password", key="admin_password_input")
        if st.button("🔓 인증 및 접속", type="primary", use_container_width=True):
            if admin_pass == "admin123":
                st.session_state['admin_authenticated'] = True
                st.success("인증되었습니다.")
                st.rerun()
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# Admin Header Bar
st.markdown("""
<div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); padding: 12px 20px; border-radius: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <span style="font-weight: 700; color: #818CF8;">✅ 관리자 권한 활성화됨</span>
        <span style="font-size: 0.8rem; color: #94A3B8; margin-left: 10px;">(시스템 상태: 정상 작동 중)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Admin Tabs
tab_price, tab_users, tab_news, tab_tx, tab_system = st.tabs([
    "📈 학과 가격 & 시세 관리", 
    "👥 사용자 & 코인 관리", 
    "📰 학과 뉴스 & 이벤트 등록", 
    "📜 전체 거래내역", 
    "⚙️ 시스템 초기화 & 제어"
])

# Tab 1: Price Management
with tab_price:
    st.markdown("#### 💹 학과 주가 실시간 수정 및 스케줄 설정")
    
    col_p1, col_p2 = st.columns([1, 1])
    
    depts = get_departments_list()
    dept_map = {d['name']: d['id'] for d in depts}
    
    with col_p1:
        st.markdown("##### 1. 특정 학과 현재가 직접 변경")
        selected_dept_name = st.selectbox("학과 선택", list(dept_map.keys()), key="admin_edit_dept_select")
        dept_id = dept_map[selected_dept_name]
        current_dept = fetch_one("SELECT * FROM departments WHERE id = ?", (dept_id,))
        
        new_price_input = st.number_input(
            "새로운 현재가 (Coin)", 
            min_value=1.0, 
            value=float(current_dept['current_price']),
            step=1.0,
            key="admin_new_price_val"
        )
        
        if st.button("💾 즉시 가격 적용", type="primary", key="btn_apply_price_now"):
            execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (new_price_input, dept_id))
            # Insert into price history
            execute_query("INSERT INTO price_history (department_id, price) VALUES (?, ?)", (dept_id, new_price_input))
            st.success(f"✅ {selected_dept_name}의 주가가 {new_price_input:.1f} Coin으로 변경되었습니다.")
            st.rerun()

    with col_p2:
        st.markdown("##### 2. ⏰ 1시간 변동 즉시 수동 실행 (APScheduler 테스트)")
        st.info("버튼을 누르면 매 1시간마다 자동 실행되는 가격 변동 스케줄러가 즉시 동작하여 12개 학과의 다음 가격이 적용됩니다.")
        if st.button("⚡ 즉시 1시간 가격 변동 실행", key="btn_force_scheduler", type="primary", use_container_width=True):
            updated = update_prices_now()
            st.success(f"🎉 12개 학과 주가가 성공적으로 업데이트되었습니다!")
            st.rerun()

    st.markdown("<hr style='border:0; height:1px; background:rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)
    
    st.markdown("##### 3. 📂 가격 CSV 파일 일괄 업로드")
    uploaded_file = st.file_uploader("가격 CSV 파일 선택 (형식: department_id, price, timestamp)", type=['csv'])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            if 'department_id' in df_upload.columns and 'price' in df_upload.columns:
                count = 0
                for _, row in df_upload.iterrows():
                    dept_i = int(row['department_id'])
                    pr = float(row['price'])
                    ts = str(row['timestamp']) if 'timestamp' in df_upload.columns else None
                    if ts:
                        execute_query("INSERT INTO price_history (department_id, price, timestamp) VALUES (?, ?, ?)", (dept_i, pr, ts))
                    else:
                        execute_query("INSERT INTO price_history (department_id, price) VALUES (?, ?)", (dept_i, pr))
                    # Update dept current price
                    execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (pr, dept_i))
                    count += 1
                st.success(f"✅ 총 {count}건의 가격 레코드가 업로드 및 반영되었습니다.")
            else:
                st.error("CSV 파일에 'department_id'와 'price' 컬럼이 있어야 합니다.")
        except Exception as e:
            st.error(f"CSV 업로드 실패: {e}")

# Tab 2: User & Coin Management
with tab_users:
    st.markdown("#### 👥 사용자 조회 및 코인 지급")
    users = get_all_users()
    
    c_u1, c_u2 = st.columns([2, 1])
    with c_u1:
        st.markdown("##### 📌 전체 등록 사용자 목록")
        df_u = pd.DataFrame(users)
        if not df_u.empty:
            df_u = df_u[['student_id', 'name', 'coin', 'created_at']]
            df_u.columns = ['학번', '이름', '보유 코인 (Coin)', '가입일']
            st.dataframe(df_u, use_container_width=True, hide_index=True)
        else:
            st.caption("등록된 사용자가 없습니다.")
            
    with c_u2:
        st.markdown("##### 🎁 코인 특별 지급 / 차감")
        student_id_target = st.text_input("학번 입력", placeholder="예: 202412345", key="admin_target_student_id")
        coin_amount = st.number_input("지급/차감 코인 수량", value=50.0, step=10.0, key="admin_coin_amount_input")
        
        if st.button("🎁 코인 지급하기", type="primary", use_container_width=True, key="btn_award_coin"):
            target_user = get_user(student_id_target.strip())
            if target_user:
                new_c = float(target_user['coin']) + coin_amount
                update_user_coin(student_id_target.strip(), new_c)
                st.success(f"✅ {target_user['name']}님에게 {coin_amount:+.1f} Coin이 지급되었습니다. (총 잔액: {new_c:,.1f} Coin)")
                st.rerun()
            else:
                st.error("해당 학번의 사용자를 찾을 수 없습니다.")

# Tab 3: News / Announcement Management
with tab_news:
    st.markdown("#### 📰 학과 소식 / 이벤트 등록")
    
    with st.form("add_news_form"):
        depts_list = get_departments_list()
        dept_news_opts = {"[전체 공과대학 공통]": None}
        dept_news_opts.update({d['name']: d['id'] for d in depts_list})
        
        sel_news_dept = st.selectbox("관련 학과", list(dept_news_opts.keys()))
        news_title = st.text_input("뉴스 제목", placeholder="예: 컴퓨터공학과 AI 연구실 대형 연구과제 수주!")
        news_content = st.text_area("뉴스 상세 내용", placeholder="자세한 호재/악재 내용을 입력하세요.")
        news_impact = st.selectbox("시장 영향", ["BULLISH (호재/상승)", "BEARISH (악재/하락)", "NEUTRAL (일반)"])
        
        submit_news = st.form_submit_button("📢 뉴스 게시하기", type="primary", use_container_width=True)
        
        if submit_news:
            if not news_title.strip() or not news_content.strip():
                st.error("제목과 내용을 모두 입력해주세요.")
            else:
                target_dept_id = dept_news_opts[sel_news_dept]
                impact_code = "BULLISH" if "BULLISH" in news_impact else ("BEARISH" if "BEARISH" in news_impact else "NEUTRAL")
                execute_query(
                    "INSERT INTO news (department_id, title, content, impact) VALUES (?, ?, ?, ?)",
                    (target_dept_id, news_title.strip(), news_content.strip(), impact_code)
                )
                st.success("✅ 공시 뉴스가 성공적으로 등록되었습니다.")
                st.rerun()

# Tab 4: All Transactions Log
with tab_tx:
    st.markdown("#### 📜 전체 사용자 거래 내역 Log")
    all_txs = get_all_transactions()
    if all_txs:
        df_all_tx = pd.DataFrame(all_txs)
        df_all_tx = df_all_tx[['timestamp', 'student_id', 'user_name', 'dept_name', 'type', 'price', 'quantity']]
        df_all_tx['total'] = df_all_tx['price'] * df_all_tx['quantity']
        df_all_tx.columns = ['시간', '학번', '이름', '학과명', '거래구분', '단가 (Coin)', '수량 (주)', '총 금액 (Coin)']
        st.dataframe(df_all_tx, use_container_width=True, hide_index=True)
    else:
        st.caption("거래 내역이 존재하지 않습니다.")

# Tab 5: System Reset & Settings
with tab_system:
    st.markdown("#### ⚙️ 시스템 초기화 & 관리")
    st.warning("⚠️ **주의**: 전체 초기화 실행 시 모든 사용자 계정, 거래 내역, 포트폴리오 데이터가 삭제되고 초기 시드 상태로 복구됩니다.")
    
    col_reset1, col_reset2 = st.columns([2, 1])
    with col_reset1:
        reset_confirm = st.text_input("초기화를 진행하려면 'RESET'을 입력하세요", key="admin_reset_confirm_input")
        if st.button("🔥 전체 DB 초기화 및 복구", type="primary", key="btn_full_db_reset"):
            if reset_confirm.strip() == "RESET":
                # Drop all tables & re-seed
                from database.db import get_db_connection
                conn = get_db_connection()
                cur = conn.cursor()
                tables = ['users', 'departments', 'holdings', 'transactions', 'price_history', 'price_schedule', 'news']
                for t in tables:
                    cur.execute(f"DROP TABLE IF EXISTS {t}")
                conn.commit()
                conn.close()
                
                seed_db()
                st.success("🎉 데이터베이스가 초기화되고 디폴트 시드 데이터로 재구성되었습니다.")
                st.rerun()
            else:
                st.error("'RESET' 문구를 정확히 입력해주세요.")
