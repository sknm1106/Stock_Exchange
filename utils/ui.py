import base64
import os
from pathlib import Path

import streamlit as st
from utils.trade import get_user_portfolio_summary
from utils.auth import get_user
from utils.date_utils import get_korea_now_str
from utils.checkin import get_user_checkin_status
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT_DIR / "assets" / "konkuk_logo.png"


def render_logo_html(width: int = 70) -> None:
    if not LOGO_PATH.exists():
        return

    logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:center;margin-bottom:8px;">
            <img src="data:image/png;base64,{logo_base64}" alt="Konkuk logo" style="display:block;width:{width}px;height:auto;">
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_custom_theme():
    st.markdown("""
    <style>
    /* Global Theme & Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Bright Theme Background */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: #F7F9F8 !important;
        color: #1F2937 !important;
    }

    [data-testid="stHeader"] {
        background-color: #F7F9F8 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB !important;
    }

    section[data-testid="stSidebar"] * {
        color: #1F2937 !important;
    }
    
    /* Header Card */
    .header-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 16px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }
    
    /* Stock Metric Badges - Meaningful Colors Maintained */
    .metric-badge-up {
        background: rgba(5, 150, 105, 0.1);
        color: #059669;
        border: 1px solid rgba(5, 150, 105, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
    }
    
    .metric-badge-down {
        background: rgba(220, 38, 38, 0.1);
        color: #DC2626;
        border: 1px solid rgba(220, 38, 38, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
    }

    /* Bright Mode Cards */
    .glass-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    
    .glass-card:hover {
        border-color: #00703E;
        box-shadow: 0 4px 16px rgba(0, 112, 62, 0.12);
        transform: translateY(-2px);
    }
    
    /* Price display typography */
    .price-large {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #1F2937;
    }
    
    .coin-badge {
        background: #00703E;
        color: white;
        padding: 6px 14px;
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(0, 112, 62, 0.25);
    }

    .asset-badge {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.25);
    }

    /* Custom Buttons with Konkuk Green Point Color (#00703E) */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    div.stButton > button[kind="primary"] {
        background-color: #00703E !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #005831 !important;
        box-shadow: 0 4px 12px rgba(0, 112, 62, 0.3);
    }

    /* Streamlit Input Focus Colors */
    input:focus, textarea:focus, select:focus {
        border-color: #00703E !important;
        box-shadow: 0 0 0 2px rgba(0, 112, 62, 0.2) !important;
    }

    /* Streamlit Sidebar Customization (Bright Mode) */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #1F2937 !important;
    }

    /* Hide Admin page link from general user sidebar navigation */
    [data-testid="stSidebarNav"] li:has(a[href*="Admin"]),
    [data-testid="stSidebarNav"] li:has(a[href*="5_Admin"]) {
        display: none !important;
    }
    
    /* Table Styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E5E7EB;
    }
    
    /* Custom tabs styling */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #00703E !important;
        color: #00703E !important;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    apply_custom_theme()
    
    # Refresh user data from DB if logged in
    user = st.session_state.get('user')
    if user:
        refreshed_user = get_user(user['student_id'])
        if refreshed_user:
            st.session_state['user'] = refreshed_user
            user = refreshed_user

    now_str = get_korea_now_str()
    logo_path = "assets/konkuk_logo.png"
    
    # Grid layout for Header
    col_title, col_user = st.columns([1.8, 2.2])
    
    with col_title:
        logo_col, text_col = st.columns([1, 4])

        with logo_col:
            render_logo_html(width=70)

        with text_col:
            st.markdown("""
            <h2 style="
                margin: 0;
                padding: 0;
                font-weight: 800;
                color: #00703E;
                font-size: 1.5rem;
            ">
                공과대학 전공박람회 주식 시장
            </h2>

            <div style="
                font-size: 0.85rem;
                color: #6B7280;
                font-weight: 500;
            ">
                건국대학교 공과대학 학과 모의 주식 거래소
            </div>
            """, unsafe_allow_html=True)

    with col_user:
        if user:
            summary = get_user_portfolio_summary(user['student_id'])
            checkin_info = get_user_checkin_status(user['student_id'])
            completed_depts = checkin_info['completed_count']
            
            c1, c2, c3, c4 = st.columns([1.2, 1.3, 1.3, 0.8])
            with c1:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #6B7280;">참여 학과: <b>{completed_depts} / 12</b></div>
                    <div style="font-weight: 700; color: #1F2937;">👤 {user['name']} <span style="font-size:0.75rem; color:#6B7280;">({user['student_id']})</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #6B7280;">보유 코인</div>
                    <div><span class="coin-badge">🪙 {summary['coin']:,.1f} Coin</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #6B7280;">총 자산</div>
                    <div><span class="asset-badge">💼 {summary['total_asset']:,.1f} Coin</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                if st.button("로그아웃", key="header_logout_btn"):
                    st.session_state.pop('user', None)
                    st.session_state['is_admin'] = False
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="text-align: right; padding-top: 8px;">
                <span style="font-size: 0.85rem; color: #6B7280;">⏰ 현재 한국시간: <b>{now_str}</b></span>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<hr style='border: 0; height: 1px; background: #E5E7EB; margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

def check_login():
    """
    Checks if user is logged in. If not, displays warning & login button or redirects.
    """
    if 'user' not in st.session_state or not st.session_state['user']:
        st.warning("🔒 서비스 이용을 위해서 먼저 로그인이 필요합니다.")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("👉 로그인 화면으로 이동", type="primary"):
                st.switch_page("pages/1_Login.py")
        st.stop()
