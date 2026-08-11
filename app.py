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

# Route logic
if 'user' in st.session_state and st.session_state['user']:
    user = st.session_state['user']
    if qr_param:
        res = process_checkin(user['student_id'], qr_param)
        st.session_state['last_checkin_res'] = res
    st.switch_page("pages/2_Home.py")
else:
    if mode_staff:
        st.switch_page("pages/1_Login.py")
    else:
        st.switch_page("pages/1_Login.py")
