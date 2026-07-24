import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
from utils.auth import login_user
from utils.ui import apply_custom_theme
from utils.checkin import process_checkin
from utils.database import fetch_one
from pathlib import Path

st.set_page_config(
    page_title="로그인 | 공과대학 전공박람회 주식 시장",
    page_icon="🟢",
    layout="wide"
)

apply_custom_theme()

LOGO_PATH = Path(ROOT_DIR) / "assets" / "konkuk_logo.jpg"

# Check URL Query Parameters for Department QR scan or Staff mode
query_params = st.query_params
qr_dept = query_params.get("dept") or query_params.get("department") or query_params.get("token")
mode_staff = query_params.get("mode") == "staff"

# Container layout
col1, col2, col3 = st.columns([1, 2.2, 1])

with col2:
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px; margin-bottom: 20px;">
        st.image(
            str(LOGO_PATH),
            width=300
        )
        <h1 style="font-size: 2.2rem; font-weight: 800; color: #00703E; margin-bottom: 6px;">
            공과대학 전공박람회 주식 시장
        </h1>
        <p style="color: #6B7280; font-size: 1.05rem; font-weight: 500;">
            건국대학교 공과대학 학과 모의 주식 거래소
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # If scanned department QR, display info banner
    target_dept_info = None
    if qr_dept:
        if str(qr_dept).isdigit():
            target_dept_info = fetch_one("SELECT * FROM departments WHERE id = ?", (int(qr_dept),))
        else:
            target_dept_info = fetch_one(
                "SELECT * FROM departments WHERE code = ? OR name = ? OR qr_token = ?",
                (qr_dept, qr_dept, qr_dept)
            )
            
    if target_dept_info:
        st.markdown(f"""
        <div style="background: rgba(0, 112, 62, 0.08); border: 1.5px solid #00703E; border-radius: 12px; padding: 14px 20px; margin-bottom: 20px; text-align: center;">
            <span style="font-size: 1.1rem; font-weight: 700; color: #00703E;">📍 [{target_dept_info['name']}] 부스 QR 스캔 완료!</span>
            <div style="font-size: 0.85rem; color: #4B5563; margin-top: 4px;">로그인 시 {target_dept_info['name']} 이벤트 참여 보상 <b>100 Coin</b>이 지급됩니다.</div>
        </div>
        """, unsafe_allow_html=True)
    elif mode_staff:
        st.info("🔐 운영진/관리자 전용 주소로 접속하셨습니다. 관리자 계정(admin777)으로 로그인해 주세요.")

    # Product Guide Banner (fix.md Requirement 6)
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; padding: 22px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
        <div style="font-size: 1.15rem; font-weight: 800; color: #00703E; text-align: center; margin-bottom: 16px;">
            🎁 상품 안내
        </div>
        <div style="display: flex; justify-content: space-around; gap: 12px; text-align: center;">
            <div style="flex: 1; background: #F7F9F8; padding: 12px; border-radius: 12px; border: 1px solid #E5E7EB;">
                <div style="font-size: 1.4rem;">🥇</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #00703E; margin-top: 4px;">1등 상품</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #1F2937; margin-top: 2px;">에어팟</div>
            </div>
            <div style="flex: 1; background: #F7F9F8; padding: 12px; border-radius: 12px; border: 1px solid #E5E7EB;">
                <div style="font-size: 1.4rem;">🥈</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #00703E; margin-top: 4px;">2등 상품</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #1F2937; margin-top: 2px;">스마트 워치</div>
            </div>
            <div style="flex: 1; background: #F7F9F8; padding: 12px; border-radius: 12px; border: 1px solid #E5E7EB;">
                <div style="font-size: 1.4rem;">🥉</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #00703E; margin-top: 4px;">3등 상품</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #1F2937; margin-top: 2px;">스타벅스 2만원 상품권</div>
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
            if st.button("📈 메인 주식 시장으로 이동", type="primary", use_container_width=True):
                st.switch_page("pages/2_Home.py")
        with col_btn2:
            if st.button("🚪 다른 계정으로 로그인", use_container_width=True):
                st.session_state.pop('user', None)
                st.session_state['is_admin'] = False
                st.rerun()
    else:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px; color: #1F2937;'>로그인 / 이벤트 참여</h3>", unsafe_allow_html=True)
            
            student_id_input = st.text_input(
                "학번", 
                placeholder="예: 202412345 (관리자: admin777)",
                help="학번을 입력해주세요."
            )
            
            name_input = st.text_input(
                "이름", 
                placeholder="예: 홍길동 (관리자: admin777)",
                help="본인 이름을 입력해 주세요."
            )
            
            submit_btn = st.form_submit_button("🚀 로그인 / 시작하기", use_container_width=True, type="primary")
            
            if submit_btn:
                sid = student_id_input.strip()
                nm = name_input.strip()
                
                if not sid or not nm:
                    st.error("학번과 이름을 모두 입력해주세요.")
                else:
                    # Check Admin Login (fix.md requirement 5)
                    if sid == "admin777" and nm == "admin777":
                        user_data, _ = login_user(sid, nm)
                        st.session_state['user'] = user_data
                        st.session_state['is_admin'] = True
                        st.success("✅ 관리자 계정으로 로그인되었습니다.")
                        st.switch_page("pages/5_Admin.py")
                    else:
                        user_data, is_new = login_user(sid, nm)
                        st.session_state['user'] = user_data
                        st.session_state['is_admin'] = False
                        
                        # Process QR checkin if scanned via QR URL
                        if target_dept_info:
                            checkin_res = process_checkin(sid, target_dept_info['id'])
                            st.session_state['last_checkin_res'] = checkin_res
                        
                        st.switch_page("pages/2_Home.py")

        st.markdown("""
        <div style="margin-top: 30px; text-align: center; font-size: 0.8rem; color: #6B7280;">
            공과대학 전공박람회 주식 시장 © 2026 건국대학교 공과대학 모의주식 대회<br>
            문의: 운영진 및 교수진
        </div>
        """, unsafe_allow_html=True)
