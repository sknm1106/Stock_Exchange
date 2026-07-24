import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import pandas as pd
from utils.ui import render_header, check_login
from utils.trade import get_user_holdings, get_user_portfolio_summary, get_user_transactions
from utils.graph import create_portfolio_pie_chart

st.set_page_config(
    page_title="포트폴리오 | 공과대학 전공박람회 주식 시장",
    page_icon="🟢",
    layout="wide"
)

render_header()
check_login()

user = st.session_state['user']
student_id = user['student_id']

# Get user portfolio summary
summary = get_user_portfolio_summary(student_id)
holdings = get_user_holdings(student_id)

st.markdown("<h3 style='color:#1F2937;'>💼 내 자산 & 포트폴리오 현황</h3>", unsafe_allow_html=True)

# Top Summary Metrics
c1, c2, c3, c4, c5 = st.columns(5)

profit_color = "#059669" if summary['total_profit_loss'] > 0 else ("#DC2626" if summary['total_profit_loss'] < 0 else "#6B7280")
profit_symbol = "▲" if summary['total_profit_loss'] > 0 else ("▼" if summary['total_profit_loss'] < 0 else "-")

with c1:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">총 자산</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #1F2937;">{summary['total_asset']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">보유 현금 코인</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #00703E;">{summary['coin']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">주식 평가금액</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{summary['stock_eval']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">투자 원금</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #4B5563;">{summary['total_invested']:,.1f}</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">Coin</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size: 0.8rem; color: #6B7280;">총 평가손익</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: {profit_color};">
            {profit_symbol} {abs(summary['total_profit_loss']):,.1f}
        </div>
        <div style="font-size: 0.85rem; font-weight: 700; color: {profit_color};">
            ({summary['total_return_rate']:+.1f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)

col_holdings, col_chart = st.columns([3, 2])

with col_chart:
    st.markdown("<h4 style='color:#1F2937;'>🍩 자산 구성 (Asset Allocation)</h4>", unsafe_allow_html=True)
    if holdings or summary['coin'] > 0:
        fig_pie = create_portfolio_pie_chart(holdings, summary['coin'])
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("보유 자산 내역이 없습니다.")

with col_holdings:
    st.markdown("<h4 style='color:#1F2937;'>📊 보유 주식 목록</h4>", unsafe_allow_html=True)
    
    if holdings:
        for h in holdings:
            p_color = "#059669" if h['profit_loss'] > 0 else ("#DC2626" if h['profit_loss'] < 0 else "#6B7280")
            p_sym = "▲" if h['profit_loss'] > 0 else ("▼" if h['profit_loss'] < 0 else "-")
            
            c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 1.2, 1.2, 1.8, 1.2])
            
            with c_h1:
                st.markdown(f"""
                <div style="padding: 4px 0;">
                    <div style="font-weight: 700; color: #1F2937;">{h['dept_name']}</div>
                    <div style="font-size: 0.75rem; color: #6B7280;">{h['dept_code']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_h2:
                st.markdown(f"""
                <div style="padding-top: 4px;">
                    <div style="font-size: 0.75rem; color: #6B7280;">수량</div>
                    <div style="font-weight: 700; color: #1F2937;">{h['quantity']} 주</div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_h3:
                st.markdown(f"""
                <div style="padding-top: 4px;">
                    <div style="font-size: 0.75rem; color: #6B7280;">평단가 / 현재가</div>
                    <div style="font-size: 0.85rem; color: #1F2937;">{h['average_price']:,.1f} / <b>{h['current_price']:,.1f}</b></div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_h4:
                st.markdown(f"""
                <div style="padding-top: 4px;">
                    <div style="font-size: 0.75rem; color: #6B7280;">평가금액 / 손익</div>
                    <div style="font-weight: 700; color: #1F2937;">{h['eval_value']:,.1f} Coin</div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: {p_color};">
                        {p_sym} {abs(h['profit_loss']):,.1f} ({h['return_rate']:+.1f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_h5:
                st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                if st.button("거래", key=f"btn_port_{h['department_id']}", use_container_width=True):
                    st.session_state['selected_dept_id'] = h['department_id']
                    st.switch_page("pages/3_Department.py")
                    
            st.markdown("<hr style='border:0; height:1px; background:#E5E7EB; margin: 4px 0;'>", unsafe_allow_html=True)
    else:
        st.info("현재 보유 중인 학과 주식이 없습니다. 메인 주식 시장에서 투자해보세요!")

# Transaction History Section
st.markdown("<h4 style='margin-top: 30px; color:#1F2937;'>📜 나의 최근 거래 내역 (한국시간)</h4>", unsafe_allow_html=True)
transactions = get_user_transactions(student_id)

if transactions:
    df_tx = pd.DataFrame(transactions)
    df_tx = df_tx[['timestamp', 'dept_name', 'type', 'price', 'quantity']]
    
    # Calculate Total Amount column
    df_tx['total_amount'] = df_tx['price'] * df_tx['quantity']
    
    # Rename columns for presentation
    df_tx.columns = ['시간 (한국시간)', '학과명', '구분', '거래 단가 (Coin)', '수량 (주)', '총 금액 (Coin)']
    
    # Format type column with emojis
    df_tx['구분'] = df_tx['구분'].map(lambda x: '🛒 BUY (매수)' if x == 'BUY' else '💰 SELL (매도)')
    
    st.dataframe(
        df_tx,
        use_container_width=True,
        hide_index=True
    )
else:
    st.caption("아직 완료된 거래 내역이 없습니다.")
