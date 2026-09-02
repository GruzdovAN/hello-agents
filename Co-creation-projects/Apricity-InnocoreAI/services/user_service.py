"""
Обслуживание пользователей
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from ..core.database import get_db
from ..models.user import UserDB, User, UserCreate, UserUpdate
from ..core.exceptions import UserNotFoundError, UserAlreadyExistsError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
"""Класс обслуживания пользователей"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
"""Подтвердить пароль"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
"""Получить хеш пароля"""
        return pwd_context.hash(password)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
"""Получить пользователей по идентификатору"""
        user_db = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user_db:
            raise UserNotFoundError(f"User with id {user_id} not found")
        return User.from_orm(user_db)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
"""Получить пользователей по адресу электронной почты"""
        user_db = self.db.query(UserDB).filter(UserDB.email == email).first()
        if not user_db:
            raise UserNotFoundError(f"User with email {email} not found")
        return User.from_orm(user_db)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
"""Получить пользователей по имени пользователя"""
        user_db = self.db.query(UserDB).filter(UserDB.username == username).first()
        if not user_db:
            raise UserNotFoundError(f"User with username {username} not found")
        return User.from_orm(user_db)
    
    def create_user(self, user_create: UserCreate) -> User:
"""Создать пользователя"""
# Проверяем, существует ли уже почтовый ящик
        if self.db.query(UserDB).filter(UserDB.email == user_create.email).first():
            raise UserAlreadyExistsError(f"Email {user_create.email} already registered")
        
# Проверяем, существует ли уже имя пользователя
        if self.db.query(UserDB).filter(UserDB.username == user_create.username).first():
            raise UserAlreadyExistsError(f"Username {user_create.username} already taken")
        
# Создать нового пользователя
        hashed_password = self.get_password_hash(user_create.password)
        user_db = UserDB(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            institution=user_create.institution,
            research_field=user_create.research_field
        )
        
        self.db.add(user_db)
        self.db.commit()
        self.db.refresh(user_db)
        
        return User.from_orm(user_db)
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
"""Обновить информацию о пользователе"""
        user_db = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user_db:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
#Обновить поля
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user_db, field, value)
        
        self.db.commit()
        self.db.refresh(user_db)
        
        return User.from_orm(user_db)
    
    def delete_user(self, user_id: int) -> bool:
"""Удалить пользователя"""
        user_db = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user_db:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        self.db.delete(user_db)
        self.db.commit()
        
        return True
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
"""Подтвердить вход пользователя"""
        try:
            user = self.get_user_by_email(email)
            if self.verify_password(password, user.hashed_password):
                return user
        except UserNotFoundError:
            pass
        return None
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
"""Изменить пароль"""
        user_db = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user_db:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        if not self.verify_password(current_password, user_db.hashed_password):
            return False
        
        user_db.hashed_password = self.get_password_hash(new_password)
        self.db.commit()
        
        return True