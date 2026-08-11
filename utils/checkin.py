from utils.database import fetch_all, fetch_one, execute_query
from utils.date_utils import get_korea_now_str
import sqlite3

REWARD_PER_EVENT = 100.0

# 14 QR Events Definition (9 Department QRs + 5 Common Event QRs)
ALL_QR_EVENTS = {
    # 9 Department Booth QRs
    "dept_social_environment": {"name": "사회환경공학부", "category": "부스", "dept_id": 1, "code": "CEE"},
    "dept_mechanical_robot": {"name": "기계·로봇·자동차공학부", "category": "부스", "dept_id": 2, "code": "MRAE"},
    "dept_electrical": {"name": "전기전자공학부", "category": "부스", "dept_id": 3, "code": "EEE"},
    "dept_chemical_energy": {"name": "화공·생명·에너지공학부", "category": "부스", "dept_id": 4, "code": "CLEE"},
    "dept_computer": {"name": "컴퓨터공학부", "category": "부스", "dept_id": 5, "code": "CSE"},
    "dept_material": {"name": "재료공학과", "category": "부스", "dept_id": 6, "code": "MSE"},
    "dept_aerospace_mobility": {"name": "항공우주·모빌리티공학과", "category": "부스", "dept_id": 7, "code": "AAME"},
    "dept_biological": {"name": "생물공학과", "category": "부스", "dept_id": 8, "code": "BE"},
    "dept_industrial": {"name": "산업공학과", "category": "부스", "dept_id": 9, "code": "IE"},

    # 5 Common Event QRs
    "event_review": {"name": "한줄평", "category": "공통행사", "dept_id": None, "code": "REV"},
    "event_quiz": {"name": "퀴즈", "category": "공통행사", "dept_id": None, "code": "QUZ"},
    "event_career": {"name": "취창업", "category": "공통행사", "dept_id": None, "code": "CAR"},
    "event_academic_vote": {"name": "학술제투표", "category": "공통행사", "dept_id": None, "code": "VOT"},
    "event_major_counseling": {"name": "자전상담", "category": "공통행사", "dept_id": None, "code": "CNS"},
}

def resolve_qr_event(identifier: str):
    """
    Resolves any identifier (event_id, dept_id, code, name, token) to a valid qr_event_id key in ALL_QR_EVENTS.
    """
    if not identifier:
        return None, None
        
    ident_str = str(identifier).strip()
    
    # 1. Direct key match
    if ident_str in ALL_QR_EVENTS:
        return ident_str, ALL_QR_EVENTS[ident_str]
        
    # 2. Match by department ID (1..9)
    if ident_str.isdigit():
        dept_id = int(ident_str)
        for key, info in ALL_QR_EVENTS.items():
            if info["dept_id"] == dept_id:
                return key, info
                
    # 3. Match by code, name, or token against departments table or ALL_QR_EVENTS
    ident_lower = ident_str.lower()
    for key, info in ALL_QR_EVENTS.items():
        if info["name"].lower() == ident_lower or info["code"].lower() == ident_lower:
            return key, info
            
    # Check departments DB for qr_token or code or name
    dept = fetch_one(
        "SELECT * FROM departments WHERE code = ? OR name = ? OR qr_token = ? OR id = ?",
        (ident_str, ident_str, ident_str, int(ident_str) if ident_str.isdigit() else -1)
    )
    if dept:
        dept_id = dept['id']
        for key, info in ALL_QR_EVENTS.items():
            if info["dept_id"] == dept_id:
                return key, info

    # Check common event keyword matches
    keyword_map = {
        "review": "event_review", "한줄평": "event_review",
        "quiz": "event_quiz", "퀴즈": "event_quiz",
        "career": "event_career", "취창업": "event_career",
        "vote": "event_academic_vote", "학술제": "event_academic_vote", "학술제투표": "event_academic_vote",
        "counseling": "event_major_counseling", "자전": "event_major_counseling", "자전상담": "event_major_counseling"
    }
    for kw, qkey in keyword_map.items():
        if kw in ident_lower:
            return qkey, ALL_QR_EVENTS[qkey]

    return None, None

def process_checkin(student_id: str, qr_identifier: str):
    """
    Process QR check-in for a student for any of the 14 QR events.
    Checks UNIQUE constraint (student_id + qr_event_id).
    Grants 100 Coin on first scan; 0 Coin on re-scan.
    """
    student_id = str(student_id).strip()
    if not student_id:
        return {"success": False, "message": "학번 정보가 올바르지 않습니다."}
        
    qr_event_id, event_info = resolve_qr_event(qr_identifier)
    if not qr_event_id or not event_info:
        return {"success": False, "message": "유효하지 않은 QR 코드입니다."}
        
    event_name = event_info["name"]
    dept_id = event_info["dept_id"]
    
    user = fetch_one("SELECT * FROM users WHERE student_id = ?", (student_id,))
    if not user:
        return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        
    current_coin = float(user['coin'])
    
    # Check existing checkin in qr_checkins
    existing = fetch_one(
        "SELECT * FROM qr_checkins WHERE student_id = ? AND qr_event_id = ?",
        (student_id, qr_event_id)
    )
    
    if existing:
        return {
            "success": True,
            "already_rewarded": True,
            "message": f"이미 **{event_name}** 이벤트 참여 보상을 받으셨습니다.\n동일한 QR 보상은 1회만 지급됩니다.",
            "event_name": event_name,
            "dept_name": event_name,
            "dept_id": dept_id,
            "coin_added": 0.0,
            "user_coin": current_coin
        }
        
    # Record checkin and grant reward
    now_str = get_korea_now_str()
    try:
        execute_query(
            "INSERT INTO qr_checkins (student_id, qr_event_id, event_name, reward_coin, checked_in_at) VALUES (?, ?, ?, ?, ?)",
            (student_id, qr_event_id, event_name, REWARD_PER_EVENT, now_str)
        )
    except sqlite3.IntegrityError:
        # Handled duplicate constraint race condition
        return {
            "success": True,
            "already_rewarded": True,
            "message": f"이미 **{event_name}** 이벤트 참여 보상을 받으셨습니다.\n동일한 QR 보상은 1회만 지급됩니다.",
            "event_name": event_name,
            "dept_name": event_name,
            "dept_id": dept_id,
            "coin_added": 0.0,
            "user_coin": current_coin
        }
        
    # Also sync with department_checkins if it's a department QR
    if dept_id:
        try:
            execute_query(
                "INSERT INTO department_checkins (event_id, student_id, department_id, reward_coin, checked_in_at) VALUES (?, ?, ?, ?, ?)",
                ("2026_EXPO", student_id, dept_id, REWARD_PER_EVENT, now_str)
            )
        except Exception:
            pass

    new_coin = current_coin + REWARD_PER_EVENT
    execute_query("UPDATE users SET coin = ? WHERE student_id = ?", (new_coin, student_id))
    
    return {
        "success": True,
        "already_rewarded": False,
        "message": f"🎉 **{event_name}** 이벤트 참여 완료!\n**{REWARD_PER_EVENT:,.0f} Coin**이 지급되었습니다.",
        "event_name": event_name,
        "dept_name": event_name,
        "dept_id": dept_id,
        "coin_added": REWARD_PER_EVENT,
        "user_coin": new_coin
    }

def get_user_checkin_status(student_id: str):
    """
    Get user checkin status for all 14 QR events.
    """
    student_id = str(student_id).strip()
    checkins = fetch_all(
        "SELECT qr_event_id, checked_in_at FROM qr_checkins WHERE student_id = ?",
        (student_id,)
    )
    
    checked_events = {c['qr_event_id']: c['checked_in_at'] for c in checkins}
    
    status_list = []
    for qkey, qinfo in ALL_QR_EVENTS.items():
        is_checked = qkey in checked_events
        status_list.append({
            "qr_event_id": qkey,
            "name": qinfo['name'],
            "category": qinfo['category'],
            "code": qinfo['code'],
            "dept_id": qinfo['dept_id'],
            "checked_in": is_checked,
            "checked_in_at": checked_events.get(qkey)
        })
        
    completed_count = len(checked_events)
    total_count = len(ALL_QR_EVENTS)
    
    return {
        "status_list": status_list,
        "completed_count": completed_count,
        "total_count": total_count,
        "percentage": (completed_count / total_count * 100) if total_count > 0 else 0.0
    }

def get_all_checkin_logs():
    """
    Get all checkin logs for Admin dashboard.
    """
    query = """
    SELECT q.*, u.name as user_name
    FROM qr_checkins q
    JOIN users u ON q.student_id = u.student_id
    ORDER BY q.checked_in_at DESC
    """
    rows = fetch_all(query)
    return [dict(r) for r in rows]
