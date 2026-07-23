import streamlit as st
from datetime import datetime
from utils.trade import get_user_portfolio_summary
from utils.auth import get_user

def apply_custom_theme():
    st.markdown("""
    <style>
    /* Global Theme & Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Dark Theme Background */
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%);
        color: #F8FAFC;
    }
    
    /* Header Card */
    .header-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    /* Stock Metric Pills */
    .metric-badge-up {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
    }
    
    .metric-badge-down {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    
    /* Price display typography */
    .price-large {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .coin-badge {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
    }

    .asset-badge {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
    }

    /* Custom Buttons */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Streamlit Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Table Styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
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

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    col_title, col_user = st.columns([1.5, 2.5])
    
    with col_title:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="font-size: 2.2rem;">🎓</div>
            <div>
                <h2 style="margin: 0; padding: 0; font-weight: 800; background: linear-gradient(90deg, #6366F1, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Engineering Stock Exchange
                </h2>
                <div style="font-size: 0.8rem; color: #94A3B8;">공과대학 12개 학과 모의 주식 거래소</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_user:
        if user:
            summary = get_user_portfolio_summary(user['student_id'])
            
            c1, c2, c3, c4 = st.columns([1.2, 1.4, 1.4, 0.8])
            with c1:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">투자자</div>
                    <div style="font-weight: 700; color: #F8FAFC;">👤 {user['name']} <span style="font-size:0.75rem; color:#64748B;">({user['student_id']})</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">보유 코인</div>
                    <div><span class="coin-badge">🪙 {summary['coin']:,.1f} Coin</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">총 자산</div>
                    <div><span class="asset-badge">💼 {summary['total_asset']:,.1f} Coin</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                if st.button("로그아웃", key="header_logout_btn"):
                    st.session_state.pop('user', None)
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="text-align: right; padding-top: 8px;">
                <span style="font-size: 0.85rem; color: #94A3B8;">⏰ 현재 시간: {now_str}</span>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<hr style='border: 0; height: 1px; background: rgba(255,255,255,0.08); margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

def check_login():
    """
    Checks if user is logged in. If not, displays warning & login button or redirects.
    """
    if 'user' not in st.session_state or not st.session_state['user']:
        st.warning("🔒 접근을 위해서 먼저 로그인이 필요합니다.")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("👉 로그인 화면으로 이동", type="primary"):
                st.switch_page("pages/1_Login.py")
        st.stop()
