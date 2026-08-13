import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
from database.seed import seed_db
from scheduler.scheduler import start_scheduler
from utils.checkin import process_checkin

# Page Configuration
st.set_page_config(
    page_title="KUSPI",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database & Scheduler
@st.cache_resource
def init_app():
    seed_db()
    start_scheduler()
    return True

init_app()

query_params = st.query_params
qr_param = query_params.get("qr") or query_params.get("dept") or query_params.get("department") or query_params.get("token")
mode_staff = query_params.get("mode") == "staff"

# =========================================================
# st.switch_page()로 넘어가면 Streamlit이 URL 쿼리 파라미터를
# 유실시키는 경우가 있어(새로고침 시 ?qr=... 이 사라지는 원인),
# 페이지 전환 전에 세션 상태에 QR 값을 반드시 저장해둔다.
# 이렇게 하면 URL이 유실되어도 로그인 페이지에서 값을 복구할 수 있다.
# =========================================================
if qr_param:
    st.session_state["pending_qr"] = qr_param
if mode_staff:
    st.session_state["pending_mode_staff"] = True

# Route logic
if 'user' in st.session_state and st.session_state['user']:
    user = st.session_state['user']
    if qr_param:
        res = process_checkin(user['student_id'], qr_param)
        st.session_state['last_checkin_res'] = res
        st.session_state.pop("pending_qr", None)
    st.switch_page("pages/2_Home.py")
else:
    if mode_staff:
        st.switch_page("pages/1_Login.py")
    else:
        st.switch_page("pages/1_Login.py")