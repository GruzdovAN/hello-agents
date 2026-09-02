"""
Пример кода: простая система управления пользователями
Для демонстрации функции ревью кода
"""

class UserManager:
    """Класс управления пользователями"""
    
    def __init__(self):
        self.users = []
    
    def add_user(self, name, age, email):
        """Добавить пользователя"""
        user = {"name": name, "age": age, "email": email}
        self.users.append(user)
        return True
    
    def get_user(self, name):
        """Получить информацию о пользователе"""
        for user in self.users:
            if user["name"] == name:
                return user
        return None
    
    def delete_user(self, name):
        """Удалить пользователя"""
        for i, user in enumerate(self.users):
            if user["name"] == name:
                del self.users[i]
                return True
        return False

def calculate_average_age(users):
    """Вычислить средний возраст"""
    total = 0
    for user in users:
        total += user["age"]
    return total / len(users)

def send_email(email, message):
    """Отправить письмо (имитация)"""
    print(f"Отправка письма на {email}: {message}")
    return True
