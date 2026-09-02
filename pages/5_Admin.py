import os
import sys
import sqlite3
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import pandas as pd
import urllib.parse
from utils.ui import apply_custom_theme
from utils.database import fetch_all, fetch_one, execute_query
from utils.trade import get_departments_list, get_all_transactions, get_user_portfolio_summary
from utils.auth import get_all_users, update_user_coin, get_user
from utils.checkin import get_all_checkin_logs, ALL_QR_EVENTS
from scheduler.scheduler import update_prices_now
from database.seed import seed_db
from utils.date_utils import get_korea_now_str

st.set_page_config(
    page_title="KUSPI | 관리자",
    page_icon="⚙️",
    layout="wide"
)

apply_custom_theme()

# Strict Admin Authorization Check
if not st.session_state.get("is_admin", False):
    st.error("🔒 관리자만 접근할 수 있는 페이지입니다.")
    st.info("로그인 화면에서 관리자 계정으로 로그인 후 이용해주세요.")
    col_nav1, _ = st.columns([1, 4])
    with col_nav1:
        if st.button("👉 로그인 화면으로 이동", type="primary"):
            st.switch_page("pages/1_Login.py")
    st.stop()

# Admin Header Banner
st.markdown("""
<div style="background: #FFFFFF; border: 1.5px solid #00703E; padding: 16px 24px; border-radius: 14px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0, 112, 62, 0.08);">
    <div>
        <h2 style="margin:0; font-weight: 800; color: #00703E;">⚙️ KUSPI 관리자 대시보드 (Admin Center)</h2>
        <div style="color: #4B5563; font-size: 0.9rem; margin-top: 2px;">건국대학교 공과대학 학과 모의 주식 거래소 (KUSPI) 운영진 전용 시스템</div>
    </div>
    <div>
        <span style="background: #00703E; color: white; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;">
            🟢 관리자 권한 활성화됨
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Admin Tabs Structure
(
    tab_overview, 
    tab_users, 
    tab_professor, 
    tab_dept_stats, 
    tab_coin_logs, 
    tab_tx, 
    tab_price, 
    tab_qr, 
    tab_system
) = st.tabs([
    "1. 📊 행사 현황",
    "2. 👥 학생 조회 (총자산 순위)",
    "3. 🎓 교수 보상",
    "4. 🏬 QR별 참여 현황",
    "5. 🪙 코인 지급 내역",
    "6. 📜 거래내역",
    "7. 💹 가격 관리",
    "8. 📱 QR 관리 (14개)",
    "9. ⚙️ 시스템"
])

# Fetch foundational data
all_users = get_all_users()
checkin_logs = get_all_checkin_logs()
all_txs = get_all_transactions()
depts = get_departments_list()

# ---------------------------------------------------------
# Tab 1: 행사 현황 Overview
# ---------------------------------------------------------
with tab_overview:
    st.markdown("<h4 style='color:#00703E;'>📊 KUSPI 행사이벤트 실시간 종합 현황</h4>", unsafe_allow_html=True)
    
    total_students = len([u for u in all_users if u['student_id'] != 'admin1463'])
    total_checkins = len(checkin_logs)
    total_granted_coins = sum(c['reward_coin'] for c in checkin_logs)
    total_tx_count = len(all_txs)
    
    c_o1, c_o2, c_o3, c_o4 = st.columns(4)
    with c_o1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #6B7280;">총 참여 학생 수</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #00703E;">{total_students} 명</div>
            <div style="font-size: 0.75rem; color: #6B7280;">등록 학생 계정 기준</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_o2:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #6B7280;">QR 총 스캔 건수</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{total_checkins} 건</div>
            <div style="font-size: 0.75rem; color: #6B7280;">9개 학과 + 5개 공통행사 합산</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_o3:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #6B7280;">누적 지급 코인 수량</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #059669;">🪙 {total_granted_coins:,.0f} Coin</div>
            <div style="font-size: 0.75rem; color: #6B7280;">이벤트 보상 총액</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_o4:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #6B7280;">총 체결 거래 건수</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #D97706;">{total_tx_count} 건</div>
            <div style="font-size: 0.75rem; color: #6B7280;">매수/매도 합계</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Tab 2: 학생 조회 (총 자산 순위 기준)
# ---------------------------------------------------------
with tab_users:
    st.markdown("<h4 style='color:#00703E;'>👥 전체 학생 조회 및 총 자산 순위 (보유 코인 + 주식 평가액)</h4>", unsafe_allow_html=True)
    st.info("🏆 우승 상품 지급 기준: 단순히 코인 잔액이 아닌 **총 보유 자산(보유 코인 + 주식 평가액)**을 기준으로 정렬됩니다.")
    
    search_query = st.text_input("🔍 학생 검색 (학번 또는 이름)", placeholder="학번 또는 이름 입력...", key="search_user_admin")
    
    user_asset_list = []
    for u in all_users:
        if u['student_id'] == 'admin1463':
            continue
        sid = u['student_id']
        name = u['name']
        summary = get_user_portfolio_summary(sid)
        coin = summary['coin']
        stock_eval = summary['stock_eval']
        total_asset = summary['total_asset']
        user_asset_list.append({
            'student_id': sid,
            'name': name,
            'coin': coin,
            'stock_eval': stock_eval,
            'total_asset': total_asset,
            'created_at': u['created_at']
        })

    if user_asset_list:
        df_u = pd.DataFrame(user_asset_list)
        df_u = df_u.sort_values(by='total_asset', ascending=False)
        df_u['rank'] = range(1, len(df_u) + 1)

        if search_query.strip():
            sq = search_query.strip().lower()
            df_u = df_u[df_u['student_id'].astype(str).str.contains(sq) | df_u['name'].str.lower().str.contains(sq)]

        df_u = df_u[['rank', 'student_id', 'name', 'coin', 'stock_eval', 'total_asset', 'created_at']]
        df_u.columns = ['순위', '학번', '이름', '보유 코인 (Coin)', '주식 평가액 (Coin)', '총 보유 자산 (Coin)', '첫 접속일']
        st.dataframe(df_u, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 학생이 없습니다.")

# ---------------------------------------------------------
# Tab 3: 교수 보상
# ---------------------------------------------------------
with tab_professor:
    st.markdown("<h4 style='color:#00703E;'>🎓 교수 및 운영진 특별 코인 보상 지급</h4>", unsafe_allow_html=True)
    st.info("교수님 질문 답변, 퀴즈 우수자, 이벤트 참여 학생 등에게 수동으로 특별 코인을 지급/차감합니다.")
    
    with st.form("prof_reward_form"):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            target_sid = st.text_input("지급 대상 학번", placeholder="예: 202412345")
        with col_r2:
            reward_amt = st.number_input("지급 / 차감 코인 수량", value=100.0, step=10.0)
            
        reason = st.text_input("보상 사유 / 메모", placeholder="예: 교수님 퀴즈 이벤트 정답 보상")
        btn_give = st.form_submit_button("🎁 코인 지급 / 차감 실행", type="primary", use_container_width=True)
        
        if btn_give:
            if not target_sid.strip():
                st.error("학번을 입력해주세요.")
            else:
                target_user = get_user(target_sid.strip())
                if target_user:
                    new_c = float(target_user['coin']) + reward_amt
                    update_user_coin(target_sid.strip(), new_c)
                    st.success(f"✅ {target_user['name']}님({target_sid.strip()})에게 {reward_amt:+.1f} Coin이 지급되었습니다. (현재 잔액: {new_c:,.1f} Coin)")
                    st.rerun()
                else:
                    st.error("해당 학번의 학생을 찾을 수 없습니다.")

# ---------------------------------------------------------
# Tab 4: QR별 참여 현황 (14개 QR)
# ---------------------------------------------------------
with tab_dept_stats:
    st.markdown("<h4 style='color:#00703E;'>🏬 14개 QR 이벤트별 참여 통계 (9개 학과 부스 + 5개 공통 행사)</h4>", unsafe_allow_html=True)
    
    qr_counts = fetch_all("""
        SELECT qr_event_id, event_name, COUNT(id) as scan_count
        FROM qr_checkins
        GROUP BY qr_event_id, event_name
    """)
    
    count_dict = {r['qr_event_id']: r['scan_count'] for r in qr_counts}
    
    stat_rows = []
    for qkey, qinfo in ALL_QR_EVENTS.items():
        stat_rows.append({
            "QR 이벤트 ID": qkey,
            "이벤트명": qinfo['name'],
            "구분": qinfo['category'],
            "스캔 참여자 수": count_dict.get(qkey, 0)
        })
        
    df_dcs = pd.DataFrame(stat_rows)
    df_dcs = df_dcs.sort_values(by='스캔 참여자 수', ascending=False)
    
    col_chart_dept, col_table_dept = st.columns([3, 2])
    with col_table_dept:
        st.dataframe(df_dcs, use_container_width=True, hide_index=True)
    with col_chart_dept:
        import plotly.express as px
        fig_bar = px.bar(
            df_dcs, 
            x='이벤트명', 
            y='스캔 참여자 수',
            title="<b>14개 QR별 참여자 수</b>",
            color='스캔 참여자 수',
            color_continuous_scale='Greens'
        )
        fig_bar.update_layout(template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#F9FAFB")
        st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------
# Tab 5: 코인 지급 내역
# ---------------------------------------------------------
with tab_coin_logs:
    st.markdown("<h4 style='color:#00703E;'>🪙 14개 QR 코인 지급 내역 Log</h4>", unsafe_allow_html=True)
    
    if checkin_logs:
        df_cl = pd.DataFrame(checkin_logs)
        df_cl = df_cl[['checked_in_at', 'student_id', 'user_name', 'event_name', 'reward_coin']]
        df_cl.columns = ['참여 시간 (한국시간)', '학번', '학생 이름', 'QR 이벤트명', '지급 코인 (Coin)']
        st.dataframe(df_cl, use_container_width=True, hide_index=True)
    else:
        st.caption("아직 기록된 QR 스캔 코인 지급 내역이 없습니다.")

# ---------------------------------------------------------
# Tab 6: 전체 거래내역
# ---------------------------------------------------------
with tab_tx:
    st.markdown("<h4 style='color:#00703E;'>📜 전체 학생 주식 거래 내역 Log</h4>", unsafe_allow_html=True)
    
    if all_txs:
        df_all_tx = pd.DataFrame(all_txs)
        df_all_tx = df_all_tx[['timestamp', 'student_id', 'user_name', 'dept_name', 'type', 'price', 'quantity']]
        df_all_tx['total'] = df_all_tx['price'] * df_all_tx['quantity']
        df_all_tx.columns = ['거래 시간 (한국시간)', '학번', '이름', '학과명', '거래구분', '단가 (Coin)', '수량 (주)', '총 금액 (Coin)']
        df_all_tx['거래구분'] = df_all_tx['거래구분'].map(lambda x: '🛒 BUY (매수)' if x == 'BUY' else '💰 SELL (매도)')
        st.dataframe(df_all_tx, use_container_width=True, hide_index=True)
    else:
        st.caption("거래 내역이 존재하지 않습니다.")

# ---------------------------------------------------------
# Tab 7: 가격 관리
# ---------------------------------------------------------
with tab_price:
    st.markdown("<h4 style='color:#00703E;'>💹 학과 주가 실시간 수정 & 1시간 자동 변동 수동 실행</h4>", unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns([1, 1])
    
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
            now_time = get_korea_now_str()
            execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (new_price_input, dept_id))
            execute_query("INSERT INTO price_history (department_id, price, timestamp) VALUES (?, ?, ?)", (dept_id, new_price_input, now_time))
            st.success(f"✅ {selected_dept_name}의 주가가 {new_price_input:.1f} Coin으로 변경되었습니다.")
            st.rerun()

    with col_p2:
        st.markdown("##### 2. ⏰ 1시간 변동 즉시 수동 실행")
        st.info(f"버튼을 누르면 {len(depts)}개 학과의 시세 변동 스케줄러가 즉시 동작하여 다음 예상 주가가 계산되어 반영됩니다.")
        if st.button("⚡ 즉시 1시간 가격 변동 실행", key="btn_force_scheduler", type="primary", use_container_width=True):
            updated = update_prices_now()
            st.success(f"🎉 {len(depts)}개 학과 주가가 성공적으로 업데이트되었습니다!")
            st.rerun()

    st.markdown("<hr style='border:0; height:1px; background:#E5E7EB; margin: 20px 0;'>", unsafe_allow_html=True)
    
    st.markdown("##### 3. 📂 가격 CSV 파일 일괄 업로드")
    uploaded_file = st.file_uploader("가격 CSV 파일 선택 (형식: department_id, price, timestamp)", type=['csv'])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            if 'department_id' in df_upload.columns and 'price' in df_upload.columns:
                count = 0
                now_time = get_korea_now_str()
                for _, row in df_upload.iterrows():
                    dept_i = int(row['department_id'])
                    pr = float(row['price'])
                    ts = str(row['timestamp']) if 'timestamp' in df_upload.columns else now_time
                    execute_query("INSERT INTO price_history (department_id, price, timestamp) VALUES (?, ?, ?)", (dept_i, pr, ts))
                    execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (pr, dept_i))
                    count += 1
                st.success(f"✅ 총 {count}건의 가격 레코드가 업로드 및 반영되었습니다.")
            else:
                st.error("CSV 파일에 'department_id'와 'price' 컬럼이 있어야 합니다.")
        except Exception as e:
            st.error(f"CSV 업로드 실패: {e}")

# ---------------------------------------------------------
# Tab 8: QR 관리 (총 14개 QR)
# ---------------------------------------------------------
with tab_qr:
    st.markdown("<h4 style='color:#00703E;'>📱 14개 QR 코드 (9개 학과 부스 + 5개 공통 행사) & 접속 정보</h4>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #F7F9F8; border: 1px solid #E5E7EB; padding: 14px; border-radius: 10px; margin-bottom: 20px;">
        <b>🔑 관리자 접속 주소:</b> <code>https://stockexchange-lwgrxbag7yjrayj8w8pwqj.streamlit.app/?mode=staff</code><br>
        <span style="font-size:0.85rem; color:#6B7280;">관리자 페이지는 일반 사이드바에 노출되지 않으며 학번 <code>admin1463</code> / 이름 <code>admin1463</code> 인증이 필요합니다.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### 📍 전체 14개 QR 이벤트 목록 및 접속 URL")
    
    qr_data_list = []
    for qkey, qinfo in ALL_QR_EVENTS.items():
        target_url = f"https://stockexchange-lwgrxbag7yjrayj8w8pwqj.streamlit.app/?qr={qkey}"
        qr_data_list.append({
            "QR 이벤트 ID": qkey,
            "구분": qinfo['category'],
            "이벤트 / 학과명": qinfo['name'],
            "접속 URL": target_url
        })
        
    df_qr = pd.DataFrame(qr_data_list)
    st.dataframe(df_qr, use_container_width=True, hide_index=True)
    
    st.markdown("##### 📌 QR 이미지 생성기 미리보기")
    sel_qr_name = st.selectbox("미리볼 QR 코드 선택", [d['이벤트 / 학과명'] for d in qr_data_list], key="admin_qr_select")
    sel_qr_row = next(d for d in qr_data_list if d['이벤트 / 학과명'] == sel_qr_name)
    
    qr_img_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(sel_qr_row['접속 URL'])}"
    
    col_qr_img, col_qr_txt = st.columns([1, 3])
    with col_qr_img:
        st.image(qr_img_api_url, caption=f"{sel_qr_row['이벤트 / 학과명']} QR", width=180)
    with col_qr_txt:
        st.markdown(f"**이벤트 / 학과명:** {sel_qr_row['이벤트 / 학과명']} (`{sel_qr_row['구분']}`)")
        st.markdown(f"**QR 이벤트 ID:** `{sel_qr_row['QR 이벤트 ID']}`")
        st.markdown(f"**연결 URL:** `{sel_qr_row['접속 URL']}`")
        st.caption("위 QR 코드를 현장에 부착하면 학생들이 스캔하여 100 Coin 보상을 1회 수령할 수 있습니다.")

# ---------------------------------------------------------
# Tab 9: 관리자 계정 & 시스템
# ---------------------------------------------------------
with tab_system:
    st.markdown("<h4 style='color:#00703E;'>📰 공시 뉴스 게시 & DB 시스템 초기화</h4>", unsafe_allow_html=True)
    st.markdown("##### 💰 현재 서버 DB 자산 현황")

    live_asset_rows = []

    for u in all_users:
        if u["student_id"] == "admin777":
            continue

        summary = get_user_portfolio_summary(u["student_id"])

        live_asset_rows.append({
            "학번": u["student_id"],
            "이름": u["name"],
            "보유 코인": summary["coin"],
            "주식 평가액": summary["stock_eval"],
            "총 보유 자산": summary["total_asset"],
            "첫 접속일": u["created_at"],
        })

    if live_asset_rows:
        df_live_assets = pd.DataFrame(live_asset_rows)
        df_live_assets = df_live_assets.sort_values(
            by="총 보유 자산",
            ascending=False
        ).reset_index(drop=True)

        df_live_assets.insert(
            0,
            "순위",
            range(1, len(df_live_assets) + 1)
        )

        total_coin = df_live_assets["보유 코인"].sum()
        total_stock = df_live_assets["주식 평가액"].sum()
        total_assets = df_live_assets["총 보유 자산"].sum()

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("전체 학생 보유 코인", f"{total_coin:,.0f}")

        with c2:
            st.metric("전체 주식 평가액", f"{total_stock:,.0f}")

        with c3:
            st.metric("전체 총 보유 자산", f"{total_assets:,.0f}")

        st.dataframe(
            df_live_assets,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("등록된 학생이 없습니다.")


    st.markdown("##### 💾 현재 서버 DB 백업")

    st.caption(
        "현재 Streamlit Cloud 서버가 사용 중인 SQLite DB를 "
        "안전한 스냅샷으로 다운로드합니다."
    )

    if st.button(
        "📦 현재 서버 DB 백업 생성",
        key="btn_create_live_db_backup"
    ):
        try:
            source_conn = sqlite3.connect(DB_PATH)

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".db",
                delete=False
            )
            temp_file.close()

            backup_conn = sqlite3.connect(temp_file.name)

            source_conn.backup(backup_conn)

            backup_conn.close()
            source_conn.close()

            with open(temp_file.name, "rb") as f:
                backup_bytes = f.read()

            st.session_state["live_db_backup"] = backup_bytes

            st.success(
                "✅ 현재 서버 DB의 백업 스냅샷을 생성했습니다."
            )

        except Exception as e:
            st.error(f"DB 백업 생성 실패: {e}")

    if "live_db_backup" in st.session_state:

        st.download_button(
            label="⬇️ 서버 DB 다운로드",
            data=st.session_state["live_db_backup"],
            file_name="engineering_stock_live_backup.db",
            mime="application/octet-stream",
            key="btn_download_live_db_backup"
        )


    st.markdown("##### 1. 공과대학 호재 / 악재 뉴스 게시")
    with st.form("admin_add_news_form"):
        dept_news_opts = {"[전체 공과대학 공통]": None}
        dept_news_opts.update({d['name']: d['id'] for d in depts})
        
        sel_news_dept = st.selectbox("관련 학과", list(dept_news_opts.keys()))
        news_title = st.text_input("뉴스 제목", placeholder="예: 컴퓨터공학부 AI 연구실 대형 연구과제 수주!")
        news_content = st.text_area("뉴스 상세 내용", placeholder="자세한 호재/악재 내용을 입력하세요.")
        news_impact = st.selectbox("시장 영향", ["BULLISH (호재/상승)", "BEARISH (악재/하락)", "NEUTRAL (일반)"])
        
        submit_news = st.form_submit_button("📢 뉴스 게시하기", type="primary", use_container_width=True)
        
        if submit_news:
            if not news_title.strip() or not news_content.strip():
                st.error("제목과 내용을 모두 입력해주세요.")
            else:
                target_dept_id = dept_news_opts[sel_news_dept]
                impact_code = "BULLISH" if "BULLISH" in news_impact else ("BEARISH" if "BEARISH" in news_impact else "NEUTRAL")
                now_time = get_korea_now_str()
                execute_query(
                    "INSERT INTO news (department_id, title, content, impact, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (target_dept_id, news_title.strip(), news_content.strip(), impact_code, now_time)
                )
                st.success("✅ 공시 뉴스가 성공적으로 등록되었습니다.")
                st.rerun()

    # ---------------------------------------------------------
    # 뉴스 삭제
    # ---------------------------------------------------------
    st.markdown("##### 2. 🗑️ 공과대학 뉴스 / 공시 삭제")

    news_list = fetch_all("""
        SELECT
            n.id,
            n.department_id,
            n.title,
            n.content,
            n.impact,
            n.timestamp,
            d.name AS department_name
        FROM news n
        LEFT JOIN departments d ON n.department_id = d.id
        ORDER BY n.timestamp DESC, n.id DESC
    """)

    if news_list:
        news_options = {}

        for news in news_list:
            dept_name = news["department_name"] or "전체 공과대학"

            impact_label = {
                "BULLISH": "🔥 호재",
                "BEARISH": "📉 악재",
                "NEUTRAL": "📢 일반"
            }.get(news["impact"], news["impact"])

            label = (
                f"[{news['id']}] "
                f"{dept_name} | "
                f"{news['title']} | "
                f"{impact_label} | "
                f"{news['timestamp']}"
            )

            news_options[label] = news

        selected_news_label = st.selectbox(
            "삭제할 뉴스 선택",
            list(news_options.keys()),
            key="admin_delete_news_select"
        )

        selected_news = news_options[selected_news_label]

        # 선택한 뉴스 미리보기
        st.markdown(
            f"""
            **학과:** {selected_news['department_name'] or '전체 공과대학'}  
            **제목:** {selected_news['title']}  
            **내용:** {selected_news['content']}  
            **게시일:** {selected_news['timestamp']}
            """
        )

        delete_confirm = st.checkbox(
            "선택한 뉴스를 삭제하겠습니다.",
            key="admin_delete_news_confirm"
        )

        if st.button(
            "🗑️ 선택 뉴스 삭제",
            type="secondary",
            key="btn_delete_news"
        ):
            if not delete_confirm:
                st.warning("삭제 확인란을 먼저 체크해주세요.")
            else:
                execute_query(
                    "DELETE FROM news WHERE id = ?",
                    (selected_news["id"],)
                )

                st.success(
                    f"✅ '{selected_news['title']}' 뉴스가 삭제되었습니다."
                )
                st.rerun()

    else:
        st.info("현재 등록된 뉴스가 없습니다.")

    
    st.markdown("<hr style='border:0; height:1px; background:#E5E7EB; margin: 30px 0;'>", unsafe_allow_html=True)

    st.markdown("##### 3. 🧹 행사 사용자 데이터 초기화")

    st.warning(
        "학생 계정, 보유주식, 거래내역, QR 참여기록만 삭제됩니다. "
        "학과 정보, 현재 주가, 가격 변동 이력, 가격 스케줄, 뉴스는 그대로 유지됩니다."
    )

    reset_confirm = st.text_input(
        "사용자 데이터를 초기화하려면 'RESET'을 입력하세요",
        key="admin_reset_confirm_input"
    )

    if st.button(
        "🧹 사용자 데이터만 초기화",
        type="primary",
        key="btn_user_data_reset"
    ):
        if reset_confirm.strip() == "RESET":

            from database.db import get_db_connection

            conn = get_db_connection()
            cur = conn.cursor()

            try:
                # 사용자와 연결된 기록부터 삭제
                cur.execute("DELETE FROM department_checkins")
                cur.execute("DELETE FROM qr_checkins")
                cur.execute("DELETE FROM holdings")
                cur.execute("DELETE FROM transactions")

                # 관리자 계정은 유지하고 일반 사용자만 삭제
                cur.execute(
                    "DELETE FROM users WHERE student_id != ?",
                    ("admin1463",)
                )

                conn.commit()

                st.success(
                    "✅ 사용자 데이터가 초기화되었습니다. "
                    "학과 정보, 주가, 가격 변동 기록, 스케줄, 뉴스는 유지됩니다."
                )

                st.rerun()

            except Exception as e:
                conn.rollback()
                st.error(f"사용자 데이터 초기화 실패: {e}")

            finally:
                conn.close()

        else:
            st.error("'RESET' 문구를 정확히 입력해주세요.")