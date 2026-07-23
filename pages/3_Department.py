import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
from utils.ui import render_header, check_login
from utils.trade import (
    get_departments_list, 
    get_department_detail, 
    buy_stock, 
    sell_stock, 
    get_user_holdings
)
from utils.graph import create_price_chart
from utils.auth import get_user
from utils.database import fetch_all

st.set_page_config(
    page_title="학과 상세 | Engineering Stock Exchange",
    page_icon="🔍",
    layout="wide"
)

render_header()
check_login()

user = st.session_state['user']
student_id = user['student_id']

# Get list of all departments
all_depts = get_departments_list()
dept_options = {d['name']: d['id'] for d in all_depts}
dept_names = list(dept_options.keys())

# Determine initial selected index
default_idx = 0
if 'selected_dept_id' in st.session_state:
    target_id = st.session_state['selected_dept_id']
    for idx, d in enumerate(all_depts):
        if d['id'] == target_id:
            default_idx = idx
            break

col_selector, col_back = st.columns([4, 1])
with col_selector:
    selected_dept_name = st.selectbox("🏬 학과 선택", dept_names, index=default_idx)
with col_back:
    st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("⬅️ 시세 목록으로", use_container_width=True):
        st.switch_page("pages/2_Home.py")

dept_id = dept_options[selected_dept_name]
st.session_state['selected_dept_id'] = dept_id

# Fetch detailed department info
dept = get_department_detail(dept_id)

if not dept:
    st.error("학과 정보를 불러올 수 없습니다.")
    st.stop()

# Header Metrics Card
change_color = "#10B981" if dept['change'] > 0 else ("#EF4444" if dept['change'] < 0 else "#94A3B8")
change_symbol = "▲" if dept['change'] > 0 else ("▼" if dept['change'] < 0 else "-")

c_m1, c_m2, c_m3, c_m4, c_m5 = st.columns(5)

with c_m1:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">현재가</div>
        <div class="price-large" style="color: #F8FAFC;">{dept['current_price']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #64748B;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c_m2:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">변동률</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: {change_color};">
            {change_symbol} {abs(dept['change']):.1f}
        </div>
        <div style="font-size: 0.85rem; font-weight: 700; color: {change_color};">
            ({dept['change_rate']:+.1f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_m3:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">24시간 최고가</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #3B82F6;">{dept['high_price']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #64748B;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c_m4:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">24시간 최저가</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #F59E0B;">{dept['low_price']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #64748B;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

# User holding for this dept
user_holdings = get_user_holdings(student_id)
dept_holding = next((h for h in user_holdings if h['department_id'] == dept_id), None)
holding_qty = dept_holding['quantity'] if dept_holding else 0
avg_price = dept_holding['average_price'] if dept_holding else 0.0

with c_m5:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #94A3B8;">내 보유 수량</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #6366F1;">{holding_qty} 주</div>
        <div style="font-size: 0.75rem; color: #94A3B8;">평단가: {avg_price:,.1f} Coin</div>
    </div>
    """, unsafe_allow_html=True)

# Main Section: Chart on Left, Trade Widget on Right
col_chart, col_trade = st.columns([3, 2])

with col_chart:
    st.markdown(f"#### 📈 {dept['name']} 주가 차트")
    fig = create_price_chart(dept['history'], dept['name'])
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.4); padding: 12px 16px; border-radius: 10px; margin-top: -10px;">
        <span style="font-size: 0.85rem; color: #94A3B8;">💡 <b>학과 설명:</b> {}</span>
    </div>
    """.format(dept['description']), unsafe_allow_html=True)

with col_trade:
    st.markdown("#### ⚡ 주식 주문")
    
    tab_buy, tab_sell = st.tabs(["🛒 매수 (Buy)", "💰 매도 (Sell)"])
    
    user_coin = float(get_user(student_id)['coin'])
    current_price = dept['current_price']
    
    with tab_buy:
        st.markdown(f"**보유 코인:** `🪙 {user_coin:,.1f} Coin`")
        max_buy_qty = int(user_coin // current_price) if current_price > 0 else 0
        
        buy_qty = st.number_input(
            "매수 수량 (주)",
            min_value=1,
            max_value=max(1, max_buy_qty),
            value=1,
            step=1,
            key="buy_qty_input"
        )
        
        # Helper quick quantity buttons
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            if st.button("25% 매수", key="buy_25_btn", use_container_width=True):
                st.session_state['buy_qty_input'] = max(1, int(max_buy_qty * 0.25))
                st.rerun()
        with col_q2:
            if st.button("50% 매수", key="buy_50_btn", use_container_width=True):
                st.session_state['buy_qty_input'] = max(1, int(max_buy_qty * 0.50))
                st.rerun()
        with col_q3:
            if st.button("최대 매수", key="buy_100_btn", use_container_width=True):
                st.session_state['buy_qty_input'] = max(1, max_buy_qty)
                st.rerun()

        total_buy_cost = buy_qty * current_price
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 14px; border-radius: 10px; margin: 15px 0;">
            <div style="font-size: 0.85rem; color: #94A3B8;">총 결제 금액</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #10B981;">{total_buy_cost:,.1f} Coin</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 매수 주문 제출", type="primary", use_container_width=True, key="submit_buy_btn"):
            success, msg = buy_stock(student_id, dept_id, buy_qty)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
                
    with tab_sell:
        st.markdown(f"**현재 보유 수량:** `{holding_qty} 주`")
        
        sell_qty = st.number_input(
            "매도 수량 (주)",
            min_value=1,
            max_value=max(1, holding_qty),
            value=min(1, holding_qty) if holding_qty > 0 else 1,
            step=1,
            key="sell_qty_input"
        )
        
        col_sq1, col_sq2, col_sq3 = st.columns(3)
        with col_sq1:
            if st.button("25% 매도", key="sell_25_btn", use_container_width=True):
                st.session_state['sell_qty_input'] = max(1, int(holding_qty * 0.25))
                st.rerun()
        with col_sq2:
            if st.button("50% 매도", key="sell_50_btn", use_container_width=True):
                st.session_state['sell_qty_input'] = max(1, int(holding_qty * 0.50))
                st.rerun()
        with col_sq3:
            if st.button("전량 매도", key="sell_100_btn", use_container_width=True):
                st.session_state['sell_qty_input'] = max(1, holding_qty)
                st.rerun()

        total_sell_income = sell_qty * current_price
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 14px; border-radius: 10px; margin: 15px 0;">
            <div style="font-size: 0.85rem; color: #94A3B8;">예상 정산 금액</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #EF4444;">{total_sell_income:,.1f} Coin</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💰 매도 주문 제출", type="primary", use_container_width=True, key="submit_sell_btn"):
            if holding_qty == 0:
                st.error("보유한 수량이 없어 매도할 수 없습니다.")
            else:
                success, msg = sell_stock(student_id, dept_id, sell_qty)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# Department Specific News
st.markdown(f"<h4 style='margin-top: 30px;'>📰 {dept['name']} 최근 관련 소식</h4>", unsafe_allow_html=True)
dept_news = fetch_all(
    "SELECT * FROM news WHERE department_id = ? ORDER BY timestamp DESC LIMIT 3", 
    (dept_id,)
)

if dept_news:
    for news in dept_news:
        st.info(f"**[{news['timestamp'][:16]}] {news['title']}**\n\n{news['content']}")
else:
    st.caption("해당 학과의 최근 소식이 없습니다.")
