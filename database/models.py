from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    student_id: str
    name: str
    coin: float
    created_at: Optional[datetime] = None

@dataclass
class Department:
    id: int
    name: str
    code: str
    description: str
    current_price: float
    prev_price: Optional[float] = None
    change: Optional[float] = None
    change_rate: Optional[float] = None

@dataclass
class Holding:
    student_id: str
    department_id: int
    department_name: str
    quantity: int
    average_price: float
    current_price: float
    eval_value: float
    profit_loss: float
    return_rate: float

@dataclass
class Transaction:
    id: int
    student_id: str
    department_id: int
    department_name: str
    type: str  # BUY or SELL
    price: float
    quantity: int
    timestamp: str
