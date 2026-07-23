import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
from database.seed import seed_db
from scheduler.scheduler import start_scheduler

# Page Configuration
st.set_page_config(
    page_title="Engineering Stock Exchange | 공과대학 주식 거래소",
    page_icon="🎓",
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

# Route logic
if 'user' in st.session_state and st.session_state['user']:
    st.switch_page("pages/2_Home.py")
else:
    st.switch_page("pages/1_Login.py")
