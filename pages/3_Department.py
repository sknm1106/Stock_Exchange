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
    page_title="KUSPI | 학과 상세",
    page_icon="🟢",
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
change_color = "#059669" if dept['change'] > 0 else ("#DC2626" if dept['change'] < 0 else "#6B7280")
change_symbol = "▲" if dept['change'] > 0 else ("▼" if dept['change'] < 0 else "-")

c_m1, c_m2, c_m3, c_m4, c_m5 = st.columns(5)

with c_m1:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">현재가</div>
        <div class="price-large">{dept['current_price']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c_m2:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">변동률</div>
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
        <div style="font-size: 0.8rem; color: #6B7280;">24시간 최고가</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{dept['high_price']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c_m4:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">24시간 최저가</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #D97706;">{dept['low_price']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
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
        <div style="font-size: 0.8rem; color: #6B7280;">내 보유 수량</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #00703E;">{holding_qty} 주</div>
        <div style="font-size: 0.75rem; color: #6B7280;">평단가: {avg_price:,.1f} Coin</div>
    </div>
    """, unsafe_allow_html=True)

# Main Section: Chart on Left, Trade Widget on Right
col_chart, col_trade = st.columns([3, 2])

with col_chart:
    st.markdown(f"<h4 style='color:#1F2937;'>📈 {dept['name']} 주가 차트</h4>", unsafe_allow_html=True)
    fig = create_price_chart(dept['history'], dept['name'])
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E5E7EB; padding: 12px 16px; border-radius: 10px; margin-top: -10px;">
        <span style="font-size: 0.85rem; color: #4B5563;">💡 <b>학과 설명:</b> {}</span>
    </div>
    """.format(dept['description']), unsafe_allow_html=True)

with col_trade:
    st.markdown("<h4 style='color:#1F2937;'>⚡ 주식 주문</h4>", unsafe_allow_html=True)
    
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
        total_buy_cost = buy_qty * current_price
        st.markdown(f"""
        <div style="background: rgba(5, 150, 105, 0.08); border: 1px solid rgba(5, 150, 105, 0.3); padding: 14px; border-radius: 10px; margin: 15px 0;">
            <div style="font-size: 0.85rem; color: #4B5563;">총 결제 금액</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #059669;">{total_buy_cost:,.1f} Coin</div>
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
        total_sell_income = sell_qty * current_price
        st.markdown(f"""
        <div style="background: rgba(220, 38, 38, 0.08); border: 1px solid rgba(220, 38, 38, 0.3); padding: 14px; border-radius: 10px; margin: 15px 0;">
            <div style="font-size: 0.85rem; color: #4B5563;">예상 정산 금액</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #DC2626;">{total_sell_income:,.1f} Coin</div>
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
st.markdown(f"<h4 style='margin-top: 30px; color:#1F2937;'>📰 {dept['name']} 최근 관련 소식</h4>", unsafe_allow_html=True)
dept_news = fetch_all(
    "SELECT * FROM news WHERE department_id = ? ORDER BY timestamp DESC LIMIT 3", 
    (dept_id,)
)

if dept_news:
    for news in dept_news:
        st.info(f"**[{news['timestamp'][:16]}] {news['title']}**\n\n{news['content']}")
else:
    st.caption("해당 학과의 최근 소식이 없습니다.")
