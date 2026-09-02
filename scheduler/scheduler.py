import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from utils.database import fetch_all, fetch_one, execute_query
from database.db import get_db_connection
from utils.date_utils import get_korea_now_str

scheduler = None

def update_prices_now():
    """
    Executes an hourly price update for all engineering departments.
    Uses preset price_schedule if available; otherwise applies random walk simulation.
    """
    departments = fetch_all("SELECT * FROM departments")
    
    updated_records = []
    now_str = get_korea_now_str()
    
    for dept in departments:
        dept_id = dept['id']
        current_price = float(dept['current_price'])
        
        # Check if there is an unapplied scheduled price
        scheduled = fetch_one(
            "SELECT * FROM price_schedule WHERE department_id = ? AND is_applied = 0 AND scheduled_time <= ? ORDER BY scheduled_time ASC LIMIT 1",
            (dept_id, now_str)
        )
        
        if scheduled:
            new_price = float(scheduled['price'])
            # Mark schedule as applied
            execute_query("UPDATE price_schedule SET is_applied = 1 WHERE id = ?", (scheduled['id'],))
        else:
            # 직전 가격 대비 -5% ~ +6% 랜덤 변동 (변동폭 확대)
            change_percent = random.uniform(-5.0, 6.0)

            # 15% 확률로 급등/급락 이벤트 추가 (±8% 또는 +10%)
            if random.random() < 0.15:
                change_percent += random.choice([-8.0, 10.0])

            new_price = round(current_price * (1 + change_percent / 100.0), 1)
            # 상하한선 유지 (50~99)
            new_price = max(50.0, min(99.0, new_price))

        # Update current price in department table
        execute_query("UPDATE departments SET current_price = ? WHERE id = ?", (new_price, dept_id))
        
        # Insert into price history
        execute_query(
            "INSERT INTO price_history (department_id, price, timestamp) VALUES (?, ?, ?)",
            (dept_id, new_price, now_str)
        )
        
        updated_records.append({
            'department_id': dept_id,
            'name': dept['name'],
            'old_price': current_price,
            'new_price': new_price,
            'timestamp': now_str
        })
        
    return updated_records

def start_scheduler():
    global scheduler
    if scheduler is None or not scheduler.running:
        scheduler = BackgroundScheduler(daemon=True)
        # Schedule price update every 1 hour (3600 seconds)
        scheduler.add_job(update_prices_now, 'interval', hours=1, id='hourly_stock_update', replace_existing=True)
        scheduler.start()
        print("⏰ APScheduler started: Hourly stock price updates enabled.")