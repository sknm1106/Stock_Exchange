"""
10단계: PostgreSQL (Supabase) 기반 실제 거래 및 전체 흐름 종합 테스트 스크립트
"""

import os
import sys
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.auth import login_user, get_user, update_user_coin
from utils.trade import buy_stock, sell_stock, get_user_holdings, get_user_portfolio_summary, get_user_transactions, get_departments_list
from utils.checkin import process_checkin, get_user_checkin_status
from utils.database import fetch_all, fetch_one, execute_query
from utils.date_utils import get_korea_now_str

def run_tests():
    print("=" * 65)
    print("🧪 10단계: Supabase 연동 거래 및 기능 종합 테스트 시작")
    print("=" * 65)

    TEST_STUDENT_ID = "test_student_2026"
    TEST_STUDENT_NAME = "테스트학생"

    # 1. 이전 테스트 데이터 정리
    execute_query("DELETE FROM transactions WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM holdings WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM qr_checkins WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM department_checkins WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM users WHERE student_id = ?", (TEST_STUDENT_ID,))

    # 2. 학생 로그인 (최초 생성)
    user, is_new = login_user(TEST_STUDENT_ID, TEST_STUDENT_NAME)
    assert user is not None, "로그인 실패"
    assert user["student_id"] == TEST_STUDENT_ID
    assert user["coin"] == 0.0
    print(f"✅ [1/7] 학생 로그인 성공: {user['name']} ({user['student_id']}), 초기 코인: {user['coin']} Coin")

    # 3. QR 체크인 2건 수행 (컴퓨터공학부 100 Coin, 한줄평 공통이벤트 100 Coin)
    res1 = process_checkin(TEST_STUDENT_ID, "dept_computer")
    assert res1["success"] is True and res1["user_coin"] == 100.0, f"QR 1 실패: {res1}"
    print(f"✅ [2/7] QR 1차 체크인 (컴퓨터공학부): +100 Coin 지급 -> 현재 잔액: {res1['user_coin']} Coin")

    res2 = process_checkin(TEST_STUDENT_ID, "event_review")
    assert res2["success"] is True and res2["user_coin"] == 200.0, f"QR 2 실패: {res2}"
    print(f"✅ [2/7] QR 2차 체크인 (한줄평): +100 Coin 지급 -> 현재 잔액: {res2['user_coin']} Coin")

    # 동일 QR 재체크인 시 중복 지급 차단 확인
    res_dup = process_checkin(TEST_STUDENT_ID, "dept_computer")
    assert res_dup["already_rewarded"] is True and res_dup["user_coin"] == 200.0
    print(f"✅ [2/7] QR 중복 체크인 방지 정상 작동 (잔액 200 Coin 유지)")

    # 4. 주식 구매 테스트 (컴퓨터공학부 dept_id=5, 2주 매수)
    dept5 = fetch_one("SELECT * FROM departments WHERE id = 5")
    dept_price = float(dept5["current_price"])
    print(f"  * 컴퓨터공학부 현재가: {dept_price} Coin")
    
    # 코인이 부족한 경우 매수 실패 확인
    success_fail, msg_fail = buy_stock(TEST_STUDENT_ID, 5, 100)
    assert not success_fail, "잔액 부족 시 매수 실패해야 함"
    print(f"✅ [3/7] 잔액 부족 매수 차단 정상: {msg_fail}")

    # 2주 매수 (예: 66 * 2 = 132 Coin 소진 -> 잔여 코인 68 Coin)
    success_buy, msg_buy = buy_stock(TEST_STUDENT_ID, 5, 2)
    assert success_buy, f"매수 실패: {msg_buy}"
    print(f"✅ [3/7] 주식 매수 성공: {msg_buy}")

    # 보유주식 및 코인 확인
    user_after_buy = get_user(TEST_STUDENT_ID)
    holdings_after_buy = get_user_holdings(TEST_STUDENT_ID)
    txs_after_buy = get_user_transactions(TEST_STUDENT_ID)
    
    expected_coin = 200.0 - (dept_price * 2)
    assert abs(user_after_buy["coin"] - expected_coin) < 0.01, f"코인 불일치: {user_after_buy['coin']} != {expected_coin}"
    assert len(holdings_after_buy) == 1 and holdings_after_buy[0]["quantity"] == 2
    assert len(txs_after_buy) == 1 and txs_after_buy[0]["type"] == "BUY"
    print(f"✅ [4/7] Holdings & Coin & Transactions 확인: 2주 보유, 잔여 코인 {user_after_buy['coin']:.1f} Coin, 거래내역 1건")

    # 5. 주식 판매 테스트 (1주 매도)
    success_sell, msg_sell = sell_stock(TEST_STUDENT_ID, 5, 1)
    assert success_sell, f"매도 실패: {msg_sell}"
    print(f"✅ [5/7] 주식 매도 성공: {msg_sell}")

    user_after_sell = get_user(TEST_STUDENT_ID)
    holdings_after_sell = get_user_holdings(TEST_STUDENT_ID)
    txs_after_sell = get_user_transactions(TEST_STUDENT_ID)

    expected_coin_sell = expected_coin + dept_price
    assert abs(user_after_sell["coin"] - expected_coin_sell) < 0.01
    assert len(holdings_after_sell) == 1 and holdings_after_sell[0]["quantity"] == 1
    assert len(txs_after_sell) == 2 and txs_after_sell[0]["type"] == "SELL"
    print(f"✅ [5/7] 매도 후 잔액 복구 확인: 1주 남음, 잔여 코인 {user_after_sell['coin']:.1f} Coin, 거래내역 2건")

    # 6. 관리자 가격 변경 및 price_history 기록 테스트
    test_new_price = 85.5
    now_time = get_korea_now_str()
    execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (test_new_price, 5))
    execute_query("INSERT INTO price_history (department_id, price, timestamp) VALUES (?, ?, ?)", (5, test_new_price, now_time))

    latest_history = fetch_one("SELECT * FROM price_history WHERE department_id = 5 ORDER BY id DESC LIMIT 1")
    assert latest_history["price"] == test_new_price
    print(f"✅ [6/7] 관리자 가격 변경 및 price_history 기록 확인: {latest_history['price']} Coin ({latest_history['timestamp']})")

    # 원래 가격으로 복원
    execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (dept_price, 5))

    # 7. 포트폴리오 요약 검증
    summary = get_user_portfolio_summary(TEST_STUDENT_ID)
    assert summary["coin"] > 0
    assert summary["stock_eval"] > 0
    assert summary["total_asset"] == summary["coin"] + summary["stock_eval"]
    print(f"✅ [7/7] 포트폴리오 요약 검증 성공: 총자산={summary['total_asset']:.1f} Coin (코인={summary['coin']:.1f}, 주식평가={summary['stock_eval']:.1f})")

    # 테스트 유저 정리
    execute_query("DELETE FROM transactions WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM holdings WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM qr_checkins WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM department_checkins WHERE student_id = ?", (TEST_STUDENT_ID,))
    execute_query("DELETE FROM users WHERE student_id = ?", (TEST_STUDENT_ID,))
    print("\n" + "=" * 65)
    print("🎉 10단계: Supabase PostgreSQL 실시간 거래 및 기능 테스트 ALL PASS!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
