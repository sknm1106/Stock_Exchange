import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import pandas as pd
from utils.ui import render_header, check_login
from utils.trade import get_departments_list
from utils.database import fetch_all
from utils.checkin import get_user_checkin_status

st.set_page_config(
    page_title="주식 시장 | 공과대학 전공박람회 주식 시장",
    page_icon="🟢",
    layout="wide"
)

render_header()
check_login()

user = st.session_state['user']
student_id = user['student_id']

# Display Check-in toast/alert if redirected from QR scan login
if 'last_checkin_res' in st.session_state:
    res = st.session_state.pop('last_checkin_res')
    if res.get('success'):
        if res.get('already_rewarded'):
            st.info(res.get('message'))
        else:
            st.balloons()
            st.success(res.get('message'))

# Fetch department checkin status for the user
checkin_data = get_user_checkin_status(student_id)
dept_status_list = checkin_data['status_list']
completed_cnt = checkin_data['completed_count']
total_cnt = checkin_data['total_count']

# Department Event Check-in Overview Card (12QR.md Requirement 5)
with st.expander(f"📌 **학과 이벤트 참여 현황: {completed_cnt} / {total_cnt} 학과 완료 ({checkin_data['percentage']:.0f}%)**", expanded=True):
    st.progress(checkin_data['percentage'] / 100.0)
    
    cols = st.columns(4)
    for idx, d_stat in enumerate(dept_status_list):
        col_idx = idx % 4
        with cols[col_idx]:
            if d_stat['checked_in']:
                st.markdown(f"""
                <div style="background: rgba(5, 150, 105, 0.08); border: 1px solid #059669; border-radius: 8px; padding: 8px 12px; margin-bottom: 8px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #059669;">✅ {d_stat['name']}</div>
                    <div style="font-size: 0.72rem; color: #059669;">100 Coin 지급 완료</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 8px 12px; margin-bottom: 8px;">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #6B7280;">⬜ {d_stat['name']}</div>
                    <div style="font-size: 0.72rem; color: #9CA3AF;">부스 QR 스캔 시 100 Coin</div>
                </div>
                """, unsafe_allow_html=True)

# Fetch department stock list
depts = get_departments_list()

# Market Overview Cards
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

sorted_depts = sorted(depts, key=lambda x: x['change_rate'], reverse=True)
top_gainer = sorted_depts[0] if sorted_depts else None
top_loser = sorted_depts[-1] if sorted_depts else None

with col_stat1:
    st.markdown("""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">상장 학과 수</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #00703E;">12 개 학과</div>
        <div style="font-size: 0.75rem; color: #059669;">전체 모의 거래 가능</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat2:
    if top_gainer:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #6B7280;">최고 상승 학과 🔥</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #059669;">{top_gainer['name']}</div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #059669;">▲ {top_gainer['change']:+.1f} Coin ({top_gainer['change_rate']:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

with col_stat3:
    if top_loser:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #6B7280;">최대 하락 학과 📉</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #DC2626;">{top_loser['name']}</div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #DC2626;">▼ {top_loser['change']:+.1f} Coin ({top_loser['change_rate']:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

with col_stat4:
    avg_price = sum(d['current_price'] for d in depts) / len(depts) if depts else 0
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">평균 학과 주가</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{avg_price:,.1f} Coin</div>
        <div style="font-size: 0.75rem; color: #6B7280;">매 1시간 자동 업데이트</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<h3 style='margin-top: 10px; color: #1F2937;'>📊 학과 주식 시세표</h3>", unsafe_allow_html=True)

# Search & Filter
col_search, col_space = st.columns([2, 3])
with col_search:
    search_term = st.text_input("🔍 학과 검색", placeholder="학과명 또는 코드 검색 (예: 컴퓨터, CSE)")

filtered_depts = depts
if search_term.strip():
    term = search_term.strip().lower()
    filtered_depts = [d for d in depts if term in d['name'].lower() or term in d['code'].lower()]

# Table rendering
for dept in filtered_depts:
    c_dept, c_price, c_change, c_rate, c_action = st.columns([2.5, 1.5, 1.5, 1.5, 1.5])
    
    with c_dept:
        st.markdown(f"""
        <div style="padding: 6px 0;">
            <span style="font-weight: 700; font-size: 1.05rem; color: #1F2937;">{dept['name']}</span>
            <span style="font-size: 0.75rem; color: #4B5563; background: #E5E7EB; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">{dept['code']}</span>
            <div style="font-size: 0.78rem; color: #6B7280;">{dept['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_price:
        st.markdown(f"""
        <div style="padding-top: 12px; font-weight: 800; font-size: 1.2rem; color: #1F2937;">
            {dept['current_price']:,.1f} Coin
        </div>
        """, unsafe_allow_html=True)
        
    with c_change:
        change_symbol = "▲" if dept['change'] > 0 else ("▼" if dept['change'] < 0 else "-")
        color = "#059669" if dept['change'] > 0 else ("#DC2626" if dept['change'] < 0 else "#6B7280")
        st.markdown(f"""
        <div style="padding-top: 12px; font-weight: 700; font-size: 1.05rem; color: {color};">
            {change_symbol} {abs(dept['change']):.1f}
        </div>
        """, unsafe_allow_html=True)
        
    with c_rate:
        if dept['change_rate'] > 0:
            badge_html = f'<span class="metric-badge-up">+{dept["change_rate"]:.1f}%</span>'
        elif dept['change_rate'] < 0:
            badge_html = f'<span class="metric-badge-down">{dept["change_rate"]:.1f}%</span>'
        else:
            badge_html = f'<span style="color:#6B7280; font-weight:600;">0.0%</span>'
        st.markdown(f'<div style="padding-top: 12px;">{badge_html}</div>', unsafe_allow_html=True)
        
    with c_action:
        st.markdown('<div style="padding-top: 8px;"></div>', unsafe_allow_html=True)
        if st.button("📈 상세 / 거래", key=f"btn_dept_{dept['id']}", use_container_width=True):
            st.session_state['selected_dept_id'] = dept['id']
            st.switch_page("pages/3_Department.py")
            
    st.markdown("<hr style='border:0; height:1px; background:#E5E7EB; margin: 6px 0;'>", unsafe_allow_html=True)

# Campus News / Announcements
st.markdown("<h3 style='margin-top: 30px; color: #1F2937;'>📰 공과대학 뉴스 & 공시</h3>", unsafe_allow_html=True)
news_list = fetch_all("""
    SELECT n.*, d.name as dept_name 
    FROM news n 
    LEFT JOIN departments d ON n.department_id = d.id 
    ORDER BY n.timestamp DESC LIMIT 5
""")

if news_list:
    for news in news_list:
        impact = news['impact']
        badge_color = "#059669" if impact == "BULLISH" else ("#DC2626" if impact == "BEARISH" else "#2563EB")
        impact_label = "🔥 호재" if impact == "BULLISH" else ("📉 악재" if impact == "BEARISH" else "ℹ️ 일반")
        dept_str = news['dept_name'] if news['dept_name'] else "전체 공과대학"
        
        st.markdown(f"""
        <div class="glass-card" style="padding: 14px 20px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background: #F3F4F6; font-size: 0.75rem; padding: 2px 8px; border-radius: 6px; color: #4B5563; margin-right: 8px; font-weight: 600;">{dept_str}</span>
                    <span style="font-weight: 700; color: #1F2937; font-size: 1rem;">{news['title']}</span>
                </div>
                <div>
                    <span style="background: #FFFFFF; border: 1px solid {badge_color}; color: {badge_color}; font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; font-weight: 600;">{impact_label}</span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #4B5563; margin-top: 6px;">{news['content']}</div>
            <div style="font-size: 0.72rem; color: #9CA3AF; margin-top: 4px; text-align: right;">🕒 {news['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)
