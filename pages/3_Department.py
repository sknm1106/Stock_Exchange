import os
import sys
import html
import textwrap

import streamlit as st


# =========================================================
# 프로젝트 루트 경로 설정
# =========================================================

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


# =========================================================
# 프로젝트 모듈
# =========================================================

from utils.ui import render_header, check_login
from utils.trade import (
    get_departments_list,
    get_department_detail,
    buy_stock,
    sell_stock,
    get_user_holdings,
)
from utils.graph import create_price_chart
from utils.auth import get_user
from utils.database import fetch_all


# =========================================================
# 페이지 설정
# =========================================================

st.set_page_config(
    page_title="KUSPI | 학과 상세",
    page_icon="🟢",
    layout="wide",
)


# =========================================================
# HTML 출력 함수
#
# 핵심:
# 1. st.html() 사용
# 2. st.html() 미지원 버전에서는 HTML을 한 줄로 압축
#    → Markdown 코드블록으로 인식되는 현상 방지
# =========================================================

def render_html(content: str):
    cleaned = textwrap.dedent(content).strip()

    if hasattr(st, "html"):
        st.html(cleaned)

    else:
        one_line_html = " ".join(
            line.strip()
            for line in cleaned.splitlines()
            if line.strip()
        )

        st.markdown(
            one_line_html,
            unsafe_allow_html=True,
        )


# =========================================================
# 공통 Header / 로그인 체크
# =========================================================

render_header()
check_login()


# =========================================================
# 사용자 정보
# =========================================================

session_user = st.session_state["user"]
student_id = session_user["student_id"]


# DB에서 최신 사용자 정보 다시 조회
user_info_raw = get_user(student_id)

if not user_info_raw:
    st.error("사용자 정보를 불러올 수 없습니다.")
    st.stop()


# sqlite Row / dict 둘 다 대응
user_info = dict(user_info_raw)

st.session_state["user"] = user_info

user_coin = float(
    user_info.get("coin", 0) or 0
)


# =========================================================
# 학과 목록 조회
# =========================================================

all_depts_raw = get_departments_list()

if not all_depts_raw:
    st.error("학과 정보를 불러올 수 없습니다.")
    st.stop()


all_depts = [
    dict(d)
    for d in all_depts_raw
]


dept_options = {
    d["name"]: d["id"]
    for d in all_depts
}

dept_names = list(
    dept_options.keys()
)


# =========================================================
# QR을 통해 들어온 경우 해당 학과 자동 선택
# =========================================================

default_idx = 0

selected_dept_id = st.session_state.get(
    "selected_dept_id"
)

if selected_dept_id is not None:

    for idx, item in enumerate(all_depts):

        if item["id"] == selected_dept_id:
            default_idx = idx
            break


# =========================================================
# 학과 선택 / 시세 목록 이동
# =========================================================

selector_col, back_col = st.columns(
    [4, 1]
)


with selector_col:

    selected_dept_name = st.selectbox(
        "🏬 학과 선택",
        dept_names,
        index=default_idx,
        key="department_selector",
    )


with back_col:

    # selectbox와 버튼 높이 맞추기
    st.markdown(
        "<div style='height:28px;'></div>",
        unsafe_allow_html=True,
    )

    if st.button(
        "⬅️ 시세 목록으로",
        use_container_width=True,
        key="back_to_market",
    ):

        st.switch_page(
            "pages/2_Home.py"
        )


# =========================================================
# 선택 학과 ID
# =========================================================

dept_id = dept_options[
    selected_dept_name
]

st.session_state[
    "selected_dept_id"
] = dept_id


# =========================================================
# 학과 상세 정보
# =========================================================

dept_raw = get_department_detail(
    dept_id
)

if not dept_raw:
    st.error("학과 정보를 불러올 수 없습니다.")
    st.stop()


dept = dict(dept_raw)


# =========================================================
# 기본 데이터 안전하게 변환
# =========================================================

dept_name = str(
    dept.get("name", selected_dept_name)
)

current_price = float(
    dept.get("current_price", 0) or 0
)

change = float(
    dept.get("change", 0) or 0
)

change_rate = float(
    dept.get("change_rate", 0) or 0
)

description = str(
    dept.get("description", "") or ""
)

history = dept.get(
    "history",
    []
)


# HTML에 DB 문자열 직접 넣을 때 안전 처리
safe_dept_name = html.escape(
    dept_name
)

safe_description = html.escape(
    description
)


# =========================================================
# 사용자 보유 주식 조회
# =========================================================

holdings_raw = get_user_holdings(
    student_id
)

holdings = [
    dict(h)
    for h in (holdings_raw or [])
]


dept_holding = next(
    (
        h
        for h in holdings
        if h.get("department_id") == dept_id
    ),
    None,
)


if dept_holding:

    holding_qty = int(
        dept_holding.get(
            "quantity",
            0,
        ) or 0
    )

    avg_price = float(
        dept_holding.get(
            "average_price",
            0,
        ) or 0
    )

else:

    holding_qty = 0
    avg_price = 0.0


# =========================================================
# 등락 표시
# =========================================================

if change > 0:

    change_color = "#059669"
    change_symbol = "▲"

elif change < 0:

    change_color = "#DC2626"
    change_symbol = "▼"

else:

    change_color = "#6B7280"
    change_symbol = "－"


# =========================================================
# QR 참여 성공 메시지
# =========================================================

if st.session_state.get(
    "show_checkin_message",
    False,
):

    checkin_result = st.session_state.get(
        "last_checkin_res",
        {},
    )

    reward = 100

    if isinstance(checkin_result, dict):
        reward = checkin_result.get(
            "reward",
            100,
        ) or 100

    st.success(
        f"🎉 {dept_name} 참여 완료! "
        f"+{reward} Coin이 지급되었습니다."
    )

    # 한 번만 노출
    st.session_state[
        "show_checkin_message"
    ] = False


# =========================================================
# 학과 제목
# =========================================================

render_html(
    f"""
    <div style="
        margin-top: 6px;
        margin-bottom: 12px;
    ">
        <div style="
            font-size: 1.75rem;
            line-height: 1.3;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #1F2937;
        ">
            {safe_dept_name}
        </div>
    </div>
    """
)


# =========================================================
# 핵심 시세 카드
#
# 모바일에서는 필요한 값만 보여줌
# - 현재가
# - 변동률
# - 보유 Coin
# - 보유 주식
#
# 24시간 최고 / 최저 제거
# =========================================================

# =========================================================
# 현재가 핵심 카드
# =========================================================

render_html(
    f"""
    <div class="stock-price-card">

        <div class="stock-price-label">
            현재가
        </div>

        <div class="stock-price-row">

            <span
                class="stock-price-number"
                style="
                    font-size: 2.5rem;
                    font-weight: 900;
                    line-height: 1;
                    letter-spacing: -1.5px;
                    color: #111827;
                "
            >
                {current_price:,.1f}
            </span>

            <span class="stock-price-unit">
                Coin
            </span>

        </div>

        <div
            class="stock-price-change"
            style="color:{change_color};"
        >
            {change_symbol}
            {abs(change):,.1f}
            ({change_rate:+.1f}%)
        </div>

        <div class="stock-user-assets">

            <div>
                <span class="asset-label">
                    보유 코인
                </span>

                <strong>
                    💰 {user_coin:,.1f}
                </strong>
            </div>

            <div>
                <span class="asset-label">
                    보유 주식
                </span>

                <strong>
                    📦 {holding_qty}주
                </strong>
            </div>

        </div>

    </div>
    """
)


# =========================================================
# 시세 차트
# =========================================================

st.markdown(
    "### 📈 시세"
)


if history:

    try:

        fig = create_price_chart(
            history,
            dept_name,
        )

        # 모바일에서 차트가 지나치게 커지지 않게 제한
        # (상단 여백을 늘려 "학과명 + 주가 추이" 제목이
        #  플롯 툴바 아이콘과 겹쳐 글자가 깨지는 문제를 방지)
        fig.update_layout(
            height=300,
            margin=dict(
                l=5,
                r=5,
                t=48,
                b=10,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"price_chart_{dept_id}",
            config={
                "displayModeBar": False,
                "scrollZoom": False,
            },
        )

    except Exception as e:

        st.warning(
            "시세 차트를 불러오지 못했습니다."
        )

else:

    st.info(
        "아직 표시할 시세 데이터가 없습니다."
    )



# =========================================================
# 주문
# =========================================================

st.markdown(
    "### ⚡ 주문"
)


tab_buy, tab_sell = st.tabs(
    [
        "🛒 매수",
        "💰 매도",
    ]
)


# =========================================================
# 매수 탭
# =========================================================

with tab_buy:

    # -----------------------------------------------------
    # 보유 Coin / 현재 가격
    # -----------------------------------------------------

    render_html(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:12px;

            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:12px;

            padding:13px 14px;
            margin-top:10px;
            margin-bottom:15px;
        ">

            <div>
                <div style="
                    font-size:0.78rem;
                    color:#6B7280;
                    margin-bottom:3px;
                ">
                    보유 코인
                </div>

                <div style="
                    font-size:1rem;
                    font-weight:800;
                    color:#1F2937;
                    white-space:nowrap;
                ">
                    🪙 {user_coin:,.1f} Coin
                </div>
            </div>


            <div style="
                text-align:right;
            ">
                <div style="
                    font-size:0.78rem;
                    color:#6B7280;
                    margin-bottom:3px;
                ">
                    1주 가격
                </div>

                <div style="
                    font-size:1rem;
                    font-weight:800;
                    color:#1F2937;
                    white-space:nowrap;
                ">
                    {current_price:,.1f} Coin
                </div>
            </div>

        </div>
        """
    )


    # -----------------------------------------------------
    # 최대 매수 가능 수량
    # -----------------------------------------------------

    if current_price > 0:

        max_buy_qty = int(
            user_coin // current_price
        )

    else:

        max_buy_qty = 0


    # -----------------------------------------------------
    # 매수 불가능
    # -----------------------------------------------------

    if max_buy_qty <= 0:

        st.warning(
            "보유 코인이 부족하여 이 주식을 매수할 수 없습니다."
        )


    # -----------------------------------------------------
    # 매수 가능
    # -----------------------------------------------------

    else:

        buy_qty = st.number_input(
            "매수 수량 (주)",
            min_value=1,
            max_value=max_buy_qty,
            value=1,
            step=1,
            key=f"buy_qty_{dept_id}",
        )


        total_buy_cost = (
            float(buy_qty)
            * current_price
        )


        render_html(
            f"""
            <div style="
                background:rgba(5,150,105,0.08);
                border:1px solid rgba(5,150,105,0.25);
                border-radius:12px;
                padding:14px;
                margin:14px 0;
            ">

                <div style="
                    color:#4B5563;
                    font-size:0.8rem;
                    margin-bottom:2px;
                ">
                    총 결제 금액
                </div>

                <div style="
                    color:#059669;
                    font-size:1.4rem;
                    font-weight:800;
                ">
                    {total_buy_cost:,.1f} Coin
                </div>

            </div>
            """
        )


        if st.button(
            (
                f"🛒 {buy_qty}주 매수하기 "
                f"· {total_buy_cost:,.1f} Coin"
            ),
            type="primary",
            use_container_width=True,
            key=f"submit_buy_{dept_id}",
        ):

            success, message = buy_stock(
                student_id,
                dept_id,
                int(buy_qty),
            )


            if success:

                st.success(message)

                # 거래 후 최신 사용자 정보 반영
                refreshed_user = get_user(
                    student_id
                )

                if refreshed_user:

                    st.session_state[
                        "user"
                    ] = dict(
                        refreshed_user
                    )

                st.rerun()


            else:

                st.error(
                    message
                )


# =========================================================
# 매도 탭
# =========================================================

with tab_sell:

    render_html(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:12px;

            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:12px;

            padding:13px 14px;
            margin-top:10px;
            margin-bottom:15px;
        ">

            <div>
                <div style="
                    font-size:0.78rem;
                    color:#6B7280;
                    margin-bottom:3px;
                ">
                    현재 보유
                </div>

                <div style="
                    font-size:1rem;
                    font-weight:800;
                    color:#1F2937;
                    white-space:nowrap;
                ">
                    📦 {holding_qty}주
                </div>
            </div>


            <div style="
                text-align:right;
            ">
                <div style="
                    font-size:0.78rem;
                    color:#6B7280;
                    margin-bottom:3px;
                ">
                    현재 가격
                </div>

                <div style="
                    font-size:1rem;
                    font-weight:800;
                    color:#1F2937;
                    white-space:nowrap;
                ">
                    {current_price:,.1f} Coin
                </div>
            </div>

        </div>
        """
    )


    # -----------------------------------------------------
    # 보유 주식이 없는 경우
    # -----------------------------------------------------

    if holding_qty <= 0:

        st.info(
            "현재 이 학과의 주식을 보유하고 있지 않습니다."
        )


    # -----------------------------------------------------
    # 매도 가능
    # -----------------------------------------------------

    else:

        sell_qty = st.number_input(
            "매도 수량 (주)",
            min_value=1,
            max_value=holding_qty,
            value=1,
            step=1,
            key=f"sell_qty_{dept_id}",
        )


        total_sell_income = (
            float(sell_qty)
            * current_price
        )


        render_html(
            f"""
            <div style="
                background:rgba(220,38,38,0.07);
                border:1px solid rgba(220,38,38,0.22);
                border-radius:12px;
                padding:14px;
                margin:14px 0;
            ">

                <div style="
                    color:#4B5563;
                    font-size:0.8rem;
                    margin-bottom:2px;
                ">
                    예상 정산 금액
                </div>

                <div style="
                    color:#DC2626;
                    font-size:1.4rem;
                    font-weight:800;
                ">
                    {total_sell_income:,.1f} Coin
                </div>

            </div>
            """
        )


        if st.button(
            (
                f"💰 {sell_qty}주 매도하기 "
                f"· {total_sell_income:,.1f} Coin"
            ),
            use_container_width=True,
            key=f"submit_sell_{dept_id}",
        ):

            success, message = sell_stock(
                student_id,
                dept_id,
                int(sell_qty),
            )


            if success:

                st.success(
                    message
                )

                refreshed_user = get_user(
                    student_id
                )

                if refreshed_user:

                    st.session_state[
                        "user"
                    ] = dict(
                        refreshed_user
                    )

                st.rerun()


            else:

                st.error(
                    message
                )


# =========================================================
# 최근 관련 소식
# =========================================================

st.markdown(
    f"### 📰 {dept_name} 최근 소식"
)


dept_news = fetch_all(
    """
    SELECT *
    FROM news
    WHERE department_id = ?
    ORDER BY timestamp DESC
    LIMIT 3
    """,
    (dept_id,),
)


if dept_news:

    for item in dept_news:

        news = dict(item)

        timestamp = str(
            news.get(
                "timestamp",
                "",
            )
        )[:16]

        title = str(
            news.get(
                "title",
                "",
            )
        )

        content = str(
            news.get(
                "content",
                "",
            )
        )

        st.info(
            f"**[{timestamp}] {title}**\n\n"
            f"{content}"
        )


else:

    st.caption(
        "해당 학과의 최근 소식이 없습니다."
    )