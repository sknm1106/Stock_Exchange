import os
import sys
import base64
from pathlib import Path

import streamlit as st


# =========================================================
# 프로젝트 루트 경로 설정
# =========================================================
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


from utils.auth import login_user
from utils.ui import apply_custom_theme
from utils.checkin import process_checkin, resolve_qr_event
from utils.database import fetch_one


# =========================================================
# 페이지 기본 설정
# =========================================================
st.set_page_config(
    page_title="KUSPI | 로그인",
    page_icon="🟢",
    layout="wide"
)

apply_custom_theme()


# =========================================================
# 학교 로고 경로
# =========================================================
LOGO_PATH = (
    Path(ROOT_DIR)
    / "assets"
    / "konkuk_logo.png"
)


# =========================================================
# URL Query Parameter 확인
# =========================================================
query_params = st.query_params

# QR은 token을 가장 우선해서 판별
qr_token = query_params.get("token")
qr_value = query_params.get("qr")
dept_value = (
    query_params.get("dept")
    or query_params.get("department")
)

qr_param = qr_token or qr_value or dept_value

# -----------------------------------------------------
# st.switch_page() 로 이 페이지에 도달하면 URL의 쿼리
# 파라미터(?qr=...)가 유실되는 경우가 있다(새로고침 시
# 주소창에서 사라지는 것과 동일 현상). 이 경우 app.py에서
# 미리 저장해둔 st.session_state["pending_qr"] 값을
# 대신 사용해서 코인 지급이 끊기지 않도록 한다.
# -----------------------------------------------------
if not qr_param:
    qr_param = st.session_state.get("pending_qr")

mode_staff = (
    query_params.get("mode") == "staff"
    or st.session_state.get("pending_mode_staff", False)
)


# =========================================================
# 전체 화면 중앙 배치
# =========================================================
col1, col2, col3 = st.columns([1, 2.2, 1])

with col2:

    # -----------------------------------------------------
    # 학교 로고: HTML로 직접 출력해 제목 위 정가운데 고정
    # -----------------------------------------------------
    if LOGO_PATH.exists():
        logo_base64 = base64.b64encode(
            LOGO_PATH.read_bytes()
        ).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 40px;
                margin-bottom: 10px;
            ">
                <img
                    src="data:image/png;base64,{logo_base64}"
                    alt="건국대학교 로고"
                    style="
                        display: block;
                        width: 70px;
                        height: auto;
                        margin: 0;
                    "
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(
            "학교 로고 파일을 찾을 수 없습니다. "
            "assets/konkuk_logo.png 경로를 확인해주세요."
        )

    # -----------------------------------------------------
    # 서비스 제목
    # -----------------------------------------------------
    st.markdown(
        """
        <div style="
            text-align: center;
            font-size: 2.5rem;
            font-weight: 800;
            color: #00703E;
            margin-top: 8px;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        ">
            KUSPI
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="
            text-align: center;
            color: #6B7280;
            font-size: 1.05rem;
            font-weight: 500;
            margin-top: 0;
            margin-bottom: 24px;
        ">
            건국대학교 공과대학 학과 모의 주식 거래소
        </p>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # QR 정보 조회 (14개 QR 지원)
    # =====================================================
    target_qr_key, target_qr_info = resolve_qr_event(qr_param) if qr_param else (None, None)

    # -----------------------------------------------------
    # QR 접속 안내
    # -----------------------------------------------------
    if target_qr_info:
        event_name = target_qr_info["name"]

        st.markdown(
            f"""
            <div style="
                background: rgba(0, 112, 62, 0.08);
                border: 1.5px solid #00703E;
                border-radius: 12px;
                padding: 14px 20px;
                margin-bottom: 20px;
                text-align: center;
            ">
                <span style="
                    font-size: 1.1rem;
                    font-weight: 700;
                    color: #00703E;
                ">
                    📍 [{event_name}] QR 스캔 완료!
                </span>
                <div style="
                    font-size: 0.85rem;
                    color: #4B5563;
                    margin-top: 4px;
                ">
                    로그인하면 <b>{event_name}</b> 이벤트 참여 보상
                    <b>100 Coin</b>이 자동 지급됩니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif qr_param:
        st.warning(
            "유효하지 않은 QR코드입니다. "
            "QR코드 주소를 다시 확인해주세요."
        )

    elif mode_staff:
        st.info(
            "🔐 운영진·관리자 전용 주소로 접속하셨습니다. "
            "관리자 계정으로 로그인해주세요."
        )

    # =====================================================
    # 상품 안내 (에어팟 4 ANC 모델 1개만 표시)
    # =====================================================
    st.markdown(
        """<div style="
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            text-align: center;
        ">
            <div style="
                font-size: 1.1rem;
                font-weight: 800;
                color: #00703E;
                margin-bottom: 12px;
            ">🥇 상품 안내</div>
            <div style="
                background: #F7F9F8;
                padding: 16px 24px;
                border-radius: 14px;
                border: 1px solid #E5E7EB;
                display: inline-block;
                min-width: 240px;
            ">
                <div style="font-size: 2.2rem; margin-bottom: 4px;">🎁</div>
                <div style="
                    font-size: 1.15rem;
                    font-weight: 800;
                    color: #1F2937;
                ">추후 공개 예정</div>
            </div>
        </div>""",
        unsafe_allow_html=True
    )


    # =====================================================
    # 이미 로그인된 경우
    # =====================================================
    if st.session_state.get("user"):
        user = st.session_state["user"]

        st.success(
            f"현재 **{user['name']}**님"
            f"({user['student_id']})으로 로그인되어 있습니다."
        )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button(
                "📈 메인 주식 시장으로 이동",
                type="primary",
                use_container_width=True
            ):
                st.switch_page("pages/2_Home.py")

        with col_btn2:
            if st.button(
                "🚪 다른 계정으로 로그인",
                use_container_width=True
            ):
                st.session_state.pop("user", None)
                st.session_state["is_admin"] = False
                st.rerun()

    # =====================================================
    # 로그인되지 않은 경우
    # =====================================================
    else:
        with st.form("login_form"):
            st.markdown(
                """
                <h3 style="
                    text-align: center;
                    margin-bottom: 20px;
                    color: #1F2937;
                ">
                    로그인 / 이벤트 참여
                </h3>
                """,
                unsafe_allow_html=True
            )

            student_id_input = st.text_input(
                "학번",
                placeholder="예: 202412345",
                help="학번을 입력해주세요."
            )

            name_input = st.text_input(
                "이름",
                placeholder="예: 홍길동",
                help="본인 이름을 입력해주세요."
            )

            submit_btn = st.form_submit_button(
                "🚀 로그인 / 시작하기",
                use_container_width=True,
                type="primary"
            )

            if submit_btn:
                sid = student_id_input.strip()
                name = name_input.strip()

                if not sid or not name:
                    st.error(
                        "학번과 이름을 모두 입력해주세요."
                    )

                else:
                    # -------------------------------------
                    # 관리자 로그인
                    # -------------------------------------
                    if (
                        sid == "admin777"
                        and name == "admin777"
                    ):
                        user_data, _ = login_user(
                            sid,
                            name
                        )

                        st.session_state["user"] = user_data
                        st.session_state["is_admin"] = True

                        st.success(
                            "✅ 관리자 계정으로 로그인되었습니다."
                        )

                        st.switch_page(
                            "pages/5_Admin.py"
                        )

                    # -------------------------------------
                    # 학생 로그인
                    # -------------------------------------
                    else:
                        user_data, is_new = login_user(
                            sid,
                            name
                        )

                        st.session_state["user"] = user_data
                        st.session_state["is_admin"] = False

                        # QR로 접속한 경우 참여 보상 처리
                        if target_qr_key:
                            checkin_result = process_checkin(
                                sid,
                                qr_param
                            )

                            st.session_state["last_checkin_res"] = checkin_result

                            # 처리 완료: pending_qr 은 더 이상 필요 없으므로 정리
                            # (다음 사람이 같은 브라우저를 새로고침해도
                            #  잘못된 값으로 재처리되지 않도록)
                            st.session_state.pop("pending_qr", None)
                            st.session_state.pop("pending_mode_staff", None)

                            if not checkin_result.get("success"):
                                st.error(checkin_result.get("message", "QR 보상 처리에 실패했습니다."))
                                st.stop()

                            # 보상 지급 후 최신 사용자 정보 다시 로딩
                            refreshed_user = fetch_one(
                                "SELECT * FROM users WHERE student_id = ?",
                                (sid,)
                            )

                            if refreshed_user:
                                st.session_state["user"] = dict(refreshed_user)

                            if target_qr_info and target_qr_info.get("dept_id"):
                                st.session_state["selected_dept_id"] = target_qr_info["dept_id"]

                                # 사용자가 실제로 지급 여부를 알 수 있도록
                                st.session_state["show_checkin_message"] = True

                                st.switch_page("pages/3_Department.py")
                                st.stop()

                        st.switch_page("pages/2_Home.py")

        # =================================================
        # 하단 안내 문구
        # =================================================
        st.markdown(
            """
            <div style="
                margin-top: 30px;
                text-align: center;
                font-size: 0.8rem;
                color: #6B7280;
            ">
                KUSPI © 2026 건국대학교 공과대학 모의주식 대회
                <br>
                문의: 운영진 및 교수진
            </div>
            """,
            unsafe_allow_html=True
        )