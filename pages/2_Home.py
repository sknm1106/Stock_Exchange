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
    page_title="시세 메인 | Engineering Stock Exchange",
    page_icon="📈",
    layout="wide"
)

render_header()
check_login()

user = st.session_state['user']

# Welcome banner for first time login
if st.session_state.get('just_logged_in_new'):
    st.success(f"🎉 **환영합니다, {user['name']}님!** 최초 로그인 기념 보상으로 **100 Coin**이 지급되었습니다! 마음껏 주식에 투자해보세요.")
    st.session_state.pop('just_logged_in_new', None)

# Fetch department stock list
depts = get_departments_list()

# Market Overview Cards
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

# Top Gainer & Loser calculation
sorted_depts = sorted(depts, key=lambda x: x['change_rate'], reverse=True)
top_gainer = sorted_depts[0] if sorted_depts else None
top_loser = sorted_depts[-1] if sorted_depts else None

with col_stat1:
    st.markdown("""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">상장 학과 수</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC;">12 개 학과</div>
        <div style="font-size: 0.75rem; color: #10B981;">전체 거래 가능</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat2:
    if top_gainer:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #94A3B8;">최고 상승 학과 🔥</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #10B981;">{top_gainer['name']}</div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #10B981;">▲ {top_gainer['change']:+.1f} Coin ({top_gainer['change_rate']:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

with col_stat3:
    if top_loser:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 0.8rem; color: #94A3B8;">최대 하락 학과 📉</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #EF4444;">{top_loser['name']}</div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #EF4444;">▼ {top_loser['change']:+.1f} Coin ({top_loser['change_rate']:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

with col_stat4:
    avg_price = sum(d['current_price'] for d in depts) / len(depts) if depts else 0
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">평균 학과 주가</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #3B82F6;">{avg_price:,.1f} Coin</div>
        <div style="font-size: 0.75rem; color: #64748B;">매 1시간 자동 업데이트</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<h3 style='margin-top: 10px;'>📊 학과 주식 시세표</h3>", unsafe_allow_html=True)

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
            <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">{dept['name']}</span>
            <span style="font-size: 0.75rem; color: #64748B; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; margin-left: 6px;">{dept['code']}</span>
            <div style="font-size: 0.78rem; color: #94A3B8;">{dept['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_price:
        st.markdown(f"""
        <div style="padding-top: 12px; font-weight: 800; font-size: 1.2rem; color: #F8FAFC;">
            {dept['current_price']:,.1f} Coin
        </div>
        """, unsafe_allow_html=True)
        
    with c_change:
        change_symbol = "▲" if dept['change'] > 0 else ("▼" if dept['change'] < 0 else "-")
        color = "#10B981" if dept['change'] > 0 else ("#EF4444" if dept['change'] < 0 else "#94A3B8")
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
            badge_html = f'<span style="color:#94A3B8; font-weight:600;">0.0%</span>'
        st.markdown(f'<div style="padding-top: 12px;">{badge_html}</div>', unsafe_allow_html=True)
        
    with c_action:
        st.markdown('<div style="padding-top: 8px;"></div>', unsafe_allow_html=True)
        if st.button("📈 상세 / 거래", key=f"btn_dept_{dept['id']}", use_container_width=True):
            st.session_state['selected_dept_id'] = dept['id']
            st.switch_page("pages/3_Department.py")
            
    st.markdown("<hr style='border:0; height:1px; background:rgba(255,255,255,0.05); margin: 6px 0;'>", unsafe_allow_html=True)

# Campus News / Announcements
st.markdown("<h3 style='margin-top: 30px;'>📰 공과대학 뉴스 & 공시</h3>", unsafe_allow_html=True)
news_list = fetch_all("""
    SELECT n.*, d.name as dept_name 
    FROM news n 
    LEFT JOIN departments d ON n.department_id = d.id 
    ORDER BY n.timestamp DESC LIMIT 5
""")

if news_list:
    for news in news_list:
        impact = news['impact']
        badge_color = "#10B981" if impact == "BULLISH" else ("#EF4444" if impact == "BEARISH" else "#3B82F6")
        impact_label = "🔥 호재" if impact == "BULLISH" else ("📉 악재" if impact == "BEARISH" else "ℹ️ 일반")
        dept_str = news['dept_name'] if news['dept_name'] else "전체 공과대학"
        
        st.markdown(f"""
        <div class="glass-card" style="padding: 14px 20px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background: rgba(255,255,255,0.08); font-size: 0.75rem; padding: 2px 8px; border-radius: 6px; color: #CBD5E1; margin-right: 8px;">{dept_str}</span>
                    <span style="font-weight: 700; color: #F8FAFC; font-size: 1rem;">{news['title']}</span>
                </div>
                <div>
                    <span style="background: rgba(255,255,255,0.05); border: 1px solid {badge_color}; color: {badge_color}; font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; font-weight: 600;">{impact_label}</span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 6px;">{news['content']}</div>
        </div>
        """, unsafe_allow_html=True)
