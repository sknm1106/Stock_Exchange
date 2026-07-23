from utils.database import fetch_one, execute_query, fetch_all

INITIAL_COIN_REWARD = 100.0

def login_user(student_id: str, name: str):
    """
    Log in user with student_id and name.
    If student_id does not exist, create user with initial 100 Coin bonus.
    Returns: (user_data_dict, is_new_user)
    """
    student_id = str(student_id).strip()
    name = str(name).strip()
    
    if not student_id or not name:
        return None, False
    
    user = fetch_one("SELECT * FROM users WHERE student_id = ?", (student_id,))
    
    if user is None:
        # First time login -> Give 100 Coin
        execute_query(
            "INSERT INTO users (student_id, name, coin) VALUES (?, ?, ?)",
            (student_id, name, INITIAL_COIN_REWARD)
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
