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

st.set_page_config(
    page_title="KUSPI",
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

# Fetch department stock list
depts = get_departments_list()


# 2-Column Main Layout (1:1)
col_left, col_right = st.columns([1, 1])

# Left Column: 학과 주식 시세표
with col_left:
    st.markdown("<h3 style='color: #1F2937; margin-bottom: 12px;'>📊 학과 주식 시세표</h3>", unsafe_allow_html=True)
    
    search_term = st.text_input("🔍 학과 검색", placeholder="학과명 검색 (예: 컴퓨터공학부)", key="search_left_col")

    filtered_depts = depts
    if search_term.strip():
        term = search_term.strip().lower()
        filtered_depts = [d for d in depts if term in d['name'].lower() or term in d['code'].lower()]

    for dept in filtered_depts:
        change_symbol = "▲" if dept['change'] > 0 else ("▼" if dept['change'] < 0 else "-")
        change_color = "#059669" if dept['change'] > 0 else ("#DC2626" if dept['change'] < 0 else "#6B7280")
        
        if dept['change_rate'] > 0:
            rate_badge = f'<span class="metric-badge-up">+{dept["change_rate"]:.1f}%</span>'
        elif dept['change_rate'] < 0:
            rate_badge = f'<span class="metric-badge-down">{dept["change_rate"]:.1f}%</span>'
        else:
            rate_badge = f'<span style="color:#6B7280; font-weight:600;">0.0%</span>'

        c_d1, c_d2, c_d3, c_d4 = st.columns([2.5, 1.5, 1.8, 1.2])
        with c_d1:
            st.markdown(f"""
            <div style="padding: 4px 0;">
                <span style="font-weight: 700; font-size: 1.0rem; color: #1F2937;">{dept['name']}</span>
            </div>
            """, unsafe_allow_html=True)
        with c_d2:
            st.markdown(f"""
            <div style="padding-top: 4px; font-weight: 800; font-size: 1.05rem; color: #1F2937;">
                {dept['current_price']:,.1f} Coin
            </div>
            """, unsafe_allow_html=True)
        with c_d3:
            st.markdown(f"""
            <div style="padding-top: 4px;">
                <span style="font-weight: 700; font-size: 0.95rem; color: {change_color};">{change_symbol} {abs(dept['change']):.1f}</span>
                {rate_badge}
            </div>
            """, unsafe_allow_html=True)
        with c_d4:
            if st.button("📈 거래", key=f"btn_dept_left_{dept['id']}", use_container_width=True):
                st.session_state['selected_dept_id'] = dept['id']
                st.switch_page("pages/3_Department.py")

        st.markdown("<hr style='border:0; height:1px; background:#E5E7EB; margin: 4px 0;'>", unsafe_allow_html=True)

# Right Column: 공과대학 뉴스 & 공시
with col_right:
    st.markdown("<h3 style='color: #1F2937; margin-bottom: 12px;'>📰 공과대학 뉴스 & 공시</h3>", unsafe_allow_html=True)
    
    news_list = fetch_all("""
        SELECT n.*, d.name as dept_name 
        FROM news n 
        LEFT JOIN departments d ON n.department_id = d.id 
        ORDER BY n.timestamp DESC LIMIT 10
    """)

    if news_list:
        for news in news_list:
            impact = news['impact']
            badge_color = "#059669" if impact == "BULLISH" else ("#DC2626" if impact == "BEARISH" else "#2563EB")
            impact_label = "🔥 호재" if impact == "BULLISH" else ("📉 악재" if impact == "BEARISH" else "ℹ️ 일반")
            dept_str = news['dept_name'] if news['dept_name'] else "전체 공과대학"
            
            # 제목과 호재/악재 배지를 같은 줄에서 자연스럽게
            # 줄바꿈되도록 인라인으로 배치
            # (기존 좌우 flex 분리 방식은 모바일에서 제목이
            #  여러 줄로 꺾일 때 배지가 세로로 겹쳐 깨져 보였음)
            st.markdown(f"""
            <div class="glass-card" style="padding: 14px 18px; margin-bottom: 12px;">
                <div>
                    <span style="background: #F3F4F6; font-size: 0.75rem; padding: 2px 8px; border-radius: 6px; color: #4B5563; margin-right: 6px; font-weight: 600; white-space: nowrap;">{dept_str}</span>
                    <span style="font-weight: 700; color: #1F2937; font-size: 0.98rem;">{news['title']}</span>
                    <span style="background: #FFFFFF; border: 1px solid {badge_color}; color: {badge_color}; font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 600; white-space: nowrap; margin-left: 6px;">{impact_label}</span>
                </div>
                <div style="font-size: 0.85rem; color: #4B5563; margin-top: 6px; line-height: 1.4;">{news['content']}</div>
                <div style="font-size: 0.72rem; color: #9CA3AF; margin-top: 6px; text-align: right;">🕒 {news['timestamp']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("등록된 공시 뉴스가 없습니다.")