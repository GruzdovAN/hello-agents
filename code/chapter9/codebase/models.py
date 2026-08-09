"""
Модуль модели данных
Определите модель данных, используемую в приложении.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class User:
    """модель пользователя"""
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True
    
    def __str__(self) -> str:
        return f"User({self.username}, {self.email})"
    
    # ЗАДАЧА: Добавить метод проверки пользователя


@dataclass
class Product:
    """модель продукта"""
    id: int
    name: str
    category: str
    price: float
    stock: int
    description: Optional[str] = None
    
    def is_in_stock(self) -> bool:
        """Проверьте, есть ли он в наличии"""
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        """
        Применить скидку
        
        Аргументы:
            процент: процент скидки
            
        Возврат:
            Цена после скидки
        """
        # ЗАДАЧА: Добавить подтверждение скидки
        return self.price * (1 - percentage / 100)


@dataclass
class Order:
    """Заказать модель"""
    id: int
    user_id: int
    products: List[Product]
    total_amount: float
    status: str
    created_at: datetime
    
    def calculate_total(self) -> float:
        """Рассчитать сумму заказа"""
        # TODO: Учитывайте скидки и налоги
        return sum(p.price for p in self.products)
    
    def is_completed(self) -> bool:
        """Проверьте, выполнен ли заказ"""
        return self.status == "completed"


@dataclass
class Transaction:
    """торговая модель"""
    id: int
    order_id: int
    amount: float
    payment_method: str
    timestamp: datetime
    status: str
    
    # TODO: Добавить функцию возврата

