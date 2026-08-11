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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    
    updated_records = []
    now_str = get_korea_now_str()
    
    for dept in departments:
        dept_id = dept['id']
        current_price = float(dept['current_price'])
        
        # Check if there is an unapplied scheduled price
        cursor.execute(
            "SELECT * FROM price_schedule WHERE department_id = ? AND is_applied = 0 AND scheduled_time <= ? ORDER BY scheduled_time ASC LIMIT 1",
            (dept_id, now_str)
        )
        scheduled = cursor.fetchone()
        
        if scheduled:
            new_price = float(scheduled['price'])
            # Mark schedule as applied
            cursor.execute("UPDATE price_schedule SET is_applied = 1 WHERE id = ?", (scheduled['id'],))
        else:
            # 직전 가격 대비 -3% ~ +3% 랜덤 변동
            change_percent = random.uniform(-3.0, 3.0)
            new_price = round(current_price * (1 + change_percent / 100.0), 1)
            new_price = max(50.0, min(90.0, new_price))
        # Update current price in department table
        cursor.execute("UPDATE departments SET current_price = ? WHERE id = ?", (new_price, dept_id))
        
        # Insert into price history
        cursor.execute(
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
        
    conn.commit()
    conn.close()
    return updated_records

def start_scheduler():
    global scheduler
    if scheduler is None or not scheduler.running:
        scheduler = BackgroundScheduler(daemon=True)
        # Schedule price update every 1 hour (3600 seconds)
        scheduler.add_job(update_prices_now, 'interval', hours=1, id='hourly_stock_update', replace_existing=True)
        scheduler.start()
        print("⏰ APScheduler started: Hourly stock price updates enabled.")
