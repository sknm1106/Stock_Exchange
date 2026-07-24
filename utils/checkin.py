from utils.database import fetch_all, fetch_one, execute_query
from utils.date_utils import get_korea_now_str

DEFAULT_EVENT_ID = "2026_EXPO"
REWARD_PER_DEPT = 100.0

def process_checkin(student_id: str, dept_identifier: str):
    """
    Process department check-in for a student.
    dept_identifier can be dept_id (int/str), dept_code, dept_name, or qr_token.
    Returns: dict(
        success=bool, 
        already_rewarded=bool, 
        message=str, 
        dept_name=str, 
        coin_added=float,
        user_coin=float
    )
    """
    student_id = str(student_id).strip()
    if not student_id:
        return {"success": False, "message": "학번 정보가 올바르지 않습니다."}
        
    # Find department
    dept = None
    if str(dept_identifier).isdigit():
        dept = fetch_one("SELECT * FROM departments WHERE id = ?", (int(dept_identifier),))
    else:
        dept = fetch_one(
            "SELECT * FROM departments WHERE code = ? OR name = ? OR qr_token = ?", 
            (dept_identifier, dept_identifier, dept_identifier)
        )
        
    if not dept:
        return {"success": False, "message": "존재하지 않는 학과입니다."}
        
    dept_id = dept['id']
    dept_name = dept['name']
    
    # Check existing checkin
    existing = fetch_one(
        "SELECT * FROM department_checkins WHERE event_id = ? AND student_id = ? AND department_id = ?",
        (DEFAULT_EVENT_ID, student_id, dept_id)
    )
    
    user = fetch_one("SELECT * FROM users WHERE student_id = ?", (student_id,))
    if not user:
        return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        
    current_coin = float(user['coin'])
    
    if existing:
        return {
            "success": True,
            "already_rewarded": True,
            "message": f"이미 **{dept_name}** 이벤트 참여 보상을 받으셨습니다.\n같은 학과의 참여 보상은 한 번만 받을 수 있습니다.",
            "dept_name": dept_name,
            "coin_added": 0.0,
            "user_coin": current_coin
        }
        
    # Grant reward & Record checkin
    now_str = get_korea_now_str()
    execute_query(
        "INSERT INTO department_checkins (event_id, student_id, department_id, reward_coin, checked_in_at, qr_token_id) VALUES (?, ?, ?, ?, ?, ?)",
        (DEFAULT_EVENT_ID, student_id, dept_id, REWARD_PER_DEPT, now_str, dept['qr_token'])
    )
    
    new_coin = current_coin + REWARD_PER_DEPT
    execute_query("UPDATE users SET coin = ? WHERE student_id = ?", (new_coin, student_id))
    
    return {
        "success": True,
        "already_rewarded": False,
        "message": f"🎉 **{dept_name}** 이벤트 참여 완료!\n**{REWARD_PER_DEPT:,.0f} Coin**이 지급되었습니다.",
        "dept_name": dept_name,
        "coin_added": REWARD_PER_DEPT,
        "user_coin": new_coin
    }

def get_user_checkin_status(student_id: str):
    """
    Get user checkin status for all 12 departments.
    Returns: list of dicts with dept info + checked_in boolean + timestamp
    """
    student_id = str(student_id).strip()
    depts = fetch_all("SELECT * FROM departments ORDER BY id ASC")
    checkins = fetch_all(
        "SELECT * FROM department_checkins WHERE event_id = ? AND student_id = ?",
        (DEFAULT_EVENT_ID, student_id)
    )
    
    checked_dept_ids = {c['department_id']: c['checked_in_at'] for c in checkins}
    
    status_list = []
    for d in depts:
        dept_id = d['id']
        is_checked = dept_id in checked_dept_ids
        status_list.append({
            "id": dept_id,
            "name": d['name'],
            "code": d['code'],
            "qr_token": d['qr_token'],
            "checked_in": is_checked,
            "checked_in_at": checked_dept_ids.get(dept_id)
        })
        
    completed_count = len(checked_dept_ids)
    total_count = len(depts)
    
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
    SELECT c.*, u.name as user_name, d.name as dept_name, d.code as dept_code
    FROM department_checkins c
    JOIN users u ON c.student_id = u.student_id
    JOIN departments d ON c.department_id = d.id
    ORDER BY c.checked_in_at DESC
    """
    rows = fetch_all(query)
    return [dict(r) for r in rows]
