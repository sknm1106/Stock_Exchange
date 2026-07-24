from utils.database import fetch_one, execute_query, fetch_all
from utils.date_utils import get_korea_now_str

INITIAL_COIN_REWARD = 0.0  # 12QR.md: 최초 로그인 시 자동 100 Coin 지급 기능은 제거

def login_user(student_id: str, name: str):
    """
    Log in user with student_id and name.
    If student_id does not exist, create user with initial 0.0 Coin.
    Coins are earned via scanning department QRs.
    Returns: (user_data_dict, is_new_user)
    """
    student_id = str(student_id).strip()
    name = str(name).strip()
    
    if not student_id or not name:
        return None, False
    
    user = fetch_one("SELECT * FROM users WHERE student_id = ?", (student_id,))
    
    if user is None:
        now_str = get_korea_now_str()
        execute_query(
            "INSERT INTO users (student_id, name, coin, created_at) VALUES (?, ?, ?, ?)",
            (student_id, name, INITIAL_COIN_REWARD, now_str)
        )
        new_user = fetch_one("SELECT * FROM users WHERE student_id = ?", (student_id,))
        return dict(new_user), True
    else:
        # Existing user -> Update name if needed
        if user['name'] != name:
            execute_query("UPDATE users SET name = ? WHERE student_id = ?", (name, student_id))
            user = fetch_one("SELECT * FROM users WHERE student_id = ?", (student_id,))
        return dict(user), False

def get_user(student_id: str):
    user = fetch_one("SELECT * FROM users WHERE student_id = ?", (str(student_id).strip(),))
    return dict(user) if user else None

def update_user_coin(student_id: str, coin: float):
    execute_query("UPDATE users SET coin = ? WHERE student_id = ?", (coin, str(student_id).strip()))

def get_all_users():
    users = fetch_all("SELECT * FROM users ORDER BY created_at DESC")
    return [dict(u) for u in users]

