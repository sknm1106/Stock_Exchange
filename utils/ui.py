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
        <div style="display:flex;align-items:center;justify-content:center;margin-top:45px;margin-bottom:8px;">
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
    /* ===============================
    Mobile responsive
    ================================ */

    .mobile-stock-summary {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 16px 18px;
        margin: 10px 0 18px 0;
    }

    .mobile-stock-main {
        display: flex;
        align-items: baseline;
        gap: 6px;
    }

    .mobile-current-price {
        font-size: 2rem;
        font-weight: 800;
        color: #1F2937;
        line-height: 1.1;
    }

    .mobile-coin-unit {
        font-size: 0.85rem;
        color: #9CA3AF;
    }

    .mobile-stock-change {
        margin-top: 5px;
        font-size: 0.95rem;
        font-weight: 700;
    }

    .mobile-stock-assets {
        display: flex;
        gap: 18px;
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid #F1F3F5;
        font-size: 0.9rem;
        color: #4B5563;
        font-weight: 600;
    }
    .user-info-row {
        display: block !important;
    }

    .user-name-row {
        width: 100%;
        font-size: 1.15rem;
        font-weight: 800;
        color: #1F2937;
        margin-bottom: 10px;
        text-align: right;
    }

    .user-name-row .user-info-id {
        font-size: 0.78rem;
        font-weight: 500;
        color: #9CA3AF;
        margin-left: 4px;
    }

    .user-asset-row {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
    }

    /* Smartphone */
    @media (max-width: 768px) {
        .user-name-row {
            text-align: left;
            font-size: 1.2rem;
        }

        .user-asset-row {
            justify-content: flex-start;
            flex-wrap: wrap;
        }

        .block-container {
            padding-left: 14px !important;
            padding-right: 14px !important;
            padding-top: 1rem !important;
            max-width: 100% !important;
        }

        h1 {
            font-size: 1.55rem !important;
        }

        h2 {
            font-size: 1.35rem !important;
        }

        h3 {
            font-size: 1.15rem !important;
        }

        .glass-card {
            padding: 12px !important;
            margin-bottom: 10px !important;
            border-radius: 12px !important;
        }

        .price-large {
            font-size: 1.55rem !important;
        }

        .mobile-current-price {
            font-size: 1.9rem;
        }

        .mobile-stock-assets {
            justify-content: space-between;
            gap: 8px;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.5rem;
        }

        div.stButton > button {
            min-height: 46px;
            font-size: 0.95rem;
        }

        [data-testid="stNumberInput"] input {
            font-size: 16px !important;
        }

        [data-testid="stPlotlyChart"] {
            margin-left: -4px;
            margin-right: -4px;
        }
    }

    /* ===============================
    Header user-info row (ID / 보유 코인 / 총 자산)
    한 줄에 깨지지 않게 배치
    ================================ */
    .user-info-row {
        display: flex !important;
        flex-wrap: wrap !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 8px !important;
        row-gap: 6px !important;
        width: 100%;
        margin-top: 10px !important;
    }

    .user-info-item {
        display: inline-flex !important;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
        font-size: 0.85rem;
        color: #4B5563;
        font-weight: 600;
    }

    .user-info-item b {
        color: #1F2937;
    }

    .user-info-item .user-info-id {
        font-size: 0.72rem;
        color: #9CA3AF;
        font-weight: 500;
    }

    .user-info-row .coin-badge,
    .user-info-row .asset-badge {
        white-space: nowrap;
        padding: 4px 10px;
        font-size: 0.8rem;
        border-radius: 10px;
    }

    @media (max-width: 768px) {
        .user-info-row {
            justify-content: flex-start !important;
            gap: 6px !important;
        }

        .user-info-item {
            font-size: 0.78rem;
        }

        .user-info-row .coin-badge,
        .user-info-row .asset-badge {
            padding: 3px 8px;
            font-size: 0.72rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    apply_custom_theme()
    
    user = st.session_state.get('user')
    if user:
        refreshed_user = get_user(user['student_id'])
        if refreshed_user:
            st.session_state['user'] = refreshed_user
            user = refreshed_user

    now_str = get_korea_now_str()
    logo_path = "assets/konkuk_logo.png"
    
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
                font-size: 1.6rem;
                letter-spacing: -0.5px;
            ">
                KUSPI
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

            st.markdown(f"""
            <div class="user-info-row">
                <div class="user-name-row">
                    👤 <b>{user['name']}</b>
                    <span class="user-info-id">({user['student_id']})</span>
                </div>
                <div class="user-asset-row">
                    <span class="user-info-item">
                        <span class="user-info-label">보유 코인</span>
                        <span class="coin-badge">🪙 {summary['coin']:,.1f} Coin</span>
                    </span>
                    <span class="user-info-item">
                        <span class="user-info-label">총 자산</span>
                        <span class="asset-badge">💼 {summary['total_asset']:,.1f} Coin</span>
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            logout_spacer, logout_col = st.columns([3, 1])
            with logout_col:
                st.markdown("<div style='padding-top: 8px;'></div>", unsafe_allow_html=True)
                if st.button("로그아웃", key="header_logout_btn", use_container_width=True):
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