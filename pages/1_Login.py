import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
from utils.auth import login_user
from utils.ui import apply_custom_theme

st.set_page_config(
    page_title="로그인 | Engineering Stock Exchange",
    page_icon="🎓",
    layout="wide"
)

apply_custom_theme()

# Container layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
        <div style="font-size: 3.5rem; margin-bottom: 10px;">🎓</div>
        <h1 style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(90deg, #6366F1, #3B82F6, #10B981); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Engineering Stock Exchange
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            공과대학 12개 학과의 가치를 가상 코인으로 투자하는 모의 주식 거래 서비스
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Banner
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; margin-bottom: 24px; text-align: center;">
        <div style="display: flex; justify-content: space-around; gap: 10px;">
            <div>
                <div style="font-size: 1.3rem;">📱</div>
                <div style="font-weight: 700; font-size: 0.9rem; color: #F8FAFC;">QR 간편 접속</div>
                <div style="font-size: 0.75rem; color: #64748B;">별도 가입 절차 없음</div>
            </div>
            <div style="border-left: 1px solid rgba(255,255,255,0.1);"></div>
            <div>
                <div style="font-size: 1.3rem;">🪙</div>
                <div style="font-weight: 700; font-size: 0.9rem; color: #F8FAFC;">100 Coin 지급</div>
                <div style="font-size: 0.75rem; color: #64748B;">최초 로그인 시 자동 선물</div>
            </div>
            <div style="border-left: 1px solid rgba(255,255,255,0.1);"></div>
            <div>
                <div style="font-size: 1.3rem;">⏰</div>
                <div style="font-weight: 700; font-size: 0.9rem; color: #F8FAFC;">1시간 가격 변동</div>
                <div style="font-size: 0.75rem; color: #64748B;">학과별 시세 변동</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Check if already logged in
    if 'user' in st.session_state and st.session_state['user']:
        user = st.session_state['user']
        st.success(f"현재 **{user['name']}**님({user['student_id']})으로 로그인되어 있습니다.")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📈 메인 시세 화면으로 이동", type="primary", use_container_width=True):
                st.switch_page("pages/2_Home.py")
        with col_btn2:
            if st.button("🚪 다른 계정으로 로그인", use_container_width=True):
                st.session_state.pop('user', None)
                st.rerun()
    else:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>학생 로그인</h3>", unsafe_allow_html=True)
            
            student_id_input = st.text_input(
                "학번", 
                placeholder="예: 202412345",
                help="학번 8~9자리를 입력해주세요."
            )
            
            name_input = st.text_input(
                "이름", 
                placeholder="예: 홍길동",
                help="본인 이름을 입력해 주세요."
            )
            
            submit_btn = st.form_submit_button("🚀 로그인 / 시작하기", use_container_width=True, type="primary")
            
            if submit_btn:
                if not student_id_input.strip() or not name_input.strip():
                    st.error("학번과 이름을 모두 입력해주세요.")
                else:
                    user_data, is_new = login_user(student_id_input.strip(), name_input.strip())
                    st.session_state['user'] = user_data
                    
                    if is_new:
                        st.balloons()
                        st.session_state['just_logged_in_new'] = True
                    
                    st.switch_page("pages/2_Home.py")

        st.markdown("""
        <div style="margin-top: 30px; text-align: center; font-size: 0.8rem; color: #64748B;">
            Engineering Stock Exchange © 2026 공과대학 모의주식 대회<br>
            문의: 관리자 (Admin 페이지 참조)
        </div>
        """, unsafe_allow_html=True)
