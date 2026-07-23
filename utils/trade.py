from utils.database import fetch_all, fetch_one, execute_query
from utils.auth import get_user, update_user_coin

def get_departments_list():
    """
    Returns list of all departments with current price, previous price, change amount, and rate.
    """
    departments = fetch_all("SELECT * FROM departments ORDER BY id ASC")
    result = []
    
    for dept in departments:
        dept_id = dept['id']
        curr_price = float(dept['current_price'])
        
        # Get previous price from price_history (2nd most recent entry, or base price)
        history = fetch_all(
            "SELECT price FROM price_history WHERE department_id = ? ORDER BY timestamp DESC LIMIT 2",
            (dept_id,)
        )
        
        if len(history) >= 2:
            prev_price = float(history[1]['price'])
        elif len(history) == 1:
            prev_price = curr_price
        else:
            prev_price = curr_price
            
        change = curr_price - prev_price
        change_rate = (change / prev_price * 100) if prev_price > 0 else 0.0
        
        result.append({
            'id': dept_id,
            'name': dept['name'],
            'code': dept['code'],
            'description': dept['description'],
            'current_price': curr_price,
            'prev_price': prev_price,
            'change': change,
            'change_rate': change_rate
        })
        
    return result

def get_department_detail(dept_id: int):
    dept = fetch_one("SELECT * FROM departments WHERE id = ?", (dept_id,))
    if not dept:
        return None
    
    dept_dict = dict(dept)
    curr_price = float(dept_dict['current_price'])
    
    # History metrics
    history = fetch_all(
        "SELECT price, timestamp FROM price_history WHERE department_id = ? ORDER BY timestamp ASC",
        (dept_id,)
    )
    
    if history:
        prices = [float(h['price']) for h in history]
        high_price = max(prices)
        low_price = min(prices)
        if len(prices) >= 2:
            prev_price = prices[-2]
        else:
            prev_price = curr_price
    else:
        prices = [curr_price]
        high_price = curr_price
        low_price = curr_price
        prev_price = curr_price
        
    change = curr_price - prev_price
    change_rate = (change / prev_price * 100) if prev_price > 0 else 0.0
    
    dept_dict.update({
        'current_price': curr_price,
        'prev_price': prev_price,
        'high_price': high_price,
        'low_price': low_price,
        'change': change,
        'change_rate': change_rate,
        'history': [dict(h) for h in history]
    })
    
    return dept_dict

def buy_stock(student_id: str, department_id: int, quantity: int):
    student_id = str(student_id).strip()
    if quantity <= 0:
        return False, "매수 수량은 1주 이상이어야 합니다."
        
    user = get_user(student_id)
    if not user:
        return False, "사용자를 찾을 수 없습니다."
        
    dept = fetch_one("SELECT * FROM departments WHERE id = ?", (department_id,))
    if not dept:
        return False, "학과를 찾을 수 없습니다."
        
    price = float(dept['current_price'])
    total_cost = price * quantity
    user_coin = float(user['coin'])
    
    if user_coin < total_cost:
        return False, f"잔여 코인이 부족합니다. (필요: {total_cost:,.1f} Coin / 보유: {user_coin:,.1f} Coin)"
        
    # Deduct Coin
    new_coin = user_coin - total_cost
    update_user_coin(student_id, new_coin)
    
    # Check holding
    holding = fetch_one(
        "SELECT * FROM holdings WHERE student_id = ? AND department_id = ?",
        (student_id, department_id)
    )
    
    if holding:
        old_qty = int(holding['quantity'])
        old_avg = float(holding['average_price'])
        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_avg) + total_cost) / new_qty
        execute_query(
            "UPDATE holdings SET quantity = ?, average_price = ? WHERE student_id = ? AND department_id = ?",
            (new_qty, new_avg, student_id, department_id)
        )
    else:
        execute_query(
            "INSERT INTO holdings (student_id, department_id, quantity, average_price) VALUES (?, ?, ?, ?)",
            (student_id, department_id, quantity, price)
        )
        
    # Record transaction
    execute_query(
        "INSERT INTO transactions (student_id, department_id, type, price, quantity) VALUES (?, ?, 'BUY', ?, ?)",
        (student_id, department_id, price, quantity)
    )
    
    return True, f"🎉 {dept['name']} {quantity}주 매수 완료! ({total_cost:,.1f} Coin 소진)"

def sell_stock(student_id: str, department_id: int, quantity: int):
    student_id = str(student_id).strip()
    if quantity <= 0:
        return False, "매도 수량은 1주 이상이어야 합니다."
        
    user = get_user(student_id)
    if not user:
        return False, "사용자를 찾을 수 없습니다."
        
    dept = fetch_one("SELECT * FROM departments WHERE id = ?", (department_id,))
    if not dept:
        return False, "학과를 찾을 수 없습니다."
        
    holding = fetch_one(
        "SELECT * FROM holdings WHERE student_id = ? AND department_id = ?",
        (student_id, department_id)
    )
    
    if not holding or int(holding['quantity']) < quantity:
        current_qty = int(holding['quantity']) if holding else 0
        return False, f"보유 수량이 부족합니다. (현재 보유: {current_qty}주)"
        
    price = float(dept['current_price'])
    total_income = price * quantity
    user_coin = float(user['coin'])
    
    # Add Coin
    new_coin = user_coin + total_income
    update_user_coin(student_id, new_coin)
    
    current_qty = int(holding['quantity'])
    remaining_qty = current_qty - quantity
    
    if remaining_qty == 0:
        execute_query(
            "DELETE FROM holdings WHERE student_id = ? AND department_id = ?",
            (student_id, department_id)
        )
    else:
        execute_query(
            "UPDATE holdings SET quantity = ? WHERE student_id = ? AND department_id = ?",
            (remaining_qty, student_id, department_id)
        )
        
    # Record transaction
    execute_query(
        "INSERT INTO transactions (student_id, department_id, type, price, quantity) VALUES (?, ?, 'SELL', ?, ?)",
        (student_id, department_id, price, quantity)
    )
    
    return True, f"💰 {dept['name']} {quantity}주 매도 완료! ({total_income:,.1f} Coin 획득)"

def get_user_holdings(student_id: str):
    student_id = str(student_id).strip()
    query = """
    SELECT h.student_id, h.department_id, h.quantity, h.average_price, 
           d.name as dept_name, d.code as dept_code, d.current_price
    FROM holdings h
    JOIN departments d ON h.department_id = d.id
    WHERE h.student_id = ? AND h.quantity > 0
    ORDER BY d.id ASC
    """
    rows = fetch_all(query, (student_id,))
    holdings = []
    
    for r in rows:
        qty = int(r['quantity'])
        avg_price = float(r['average_price'])
        curr_price = float(r['current_price'])
        
        invested = qty * avg_price
        eval_value = qty * curr_price
        profit_loss = eval_value - invested
        return_rate = (profit_loss / invested * 100) if invested > 0 else 0.0
        
        holdings.append({
            'department_id': r['department_id'],
            'dept_name': r['dept_name'],
            'dept_code': r['dept_code'],
            'quantity': qty,
            'average_price': avg_price,
            'current_price': curr_price,
            'invested': invested,
            'eval_value': eval_value,
            'profit_loss': profit_loss,
            'return_rate': return_rate
        })
        
    return holdings

def get_user_portfolio_summary(student_id: str):
    user = get_user(student_id)
    if not user:
        return {'coin': 0.0, 'stock_eval': 0.0, 'total_asset': 0.0, 'total_invested': 0.0, 'total_profit_loss': 0.0, 'total_return_rate': 0.0}
        
    holdings = get_user_holdings(student_id)
    coin = float(user['coin'])
    stock_eval = sum(h['eval_value'] for h in holdings)
    total_invested = sum(h['invested'] for h in holdings)
    total_asset = coin + stock_eval
    total_profit_loss = stock_eval - total_invested
    total_return_rate = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0.0
    
    return {
        'coin': coin,
        'stock_eval': stock_eval,
        'total_asset': total_asset,
        'total_invested': total_invested,
        'total_profit_loss': total_profit_loss,
        'total_return_rate': total_return_rate
    }

def get_user_transactions(student_id: str):
    student_id = str(student_id).strip()
    query = """
    SELECT t.*, d.name as dept_name
    FROM transactions t
    JOIN departments d ON t.department_id = d.id
    WHERE t.student_id = ?
    ORDER BY t.timestamp DESC
    """
    rows = fetch_all(query, (student_id,))
    return [dict(r) for r in rows]

def get_all_transactions():
    query = """
    SELECT t.*, d.name as dept_name, u.name as user_name
    FROM transactions t
    JOIN departments d ON t.department_id = d.id
    JOIN users u ON t.student_id = u.student_id
    ORDER BY t.timestamp DESC
    """
    rows = fetch_all(query)
    return [dict(r) for r in rows]
