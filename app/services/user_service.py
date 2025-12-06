from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.repositories.user_repository import user_repository
from app.core.security import password_handler
from app.core.logger import setup_logger
from app.core.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError

logger = setup_logger(__name__)


class UserService:
    def __init__(self):
        self.repository = user_repository
    
    def create_user(self, db: Session, user_create: UserCreate) -> User:
        logger.info(f"Creating user with email: {user_create.email}")
        
        if self.repository.email_exists(db, user_create.email):
            logger.warning(f"User creation failed: email {user_create.email} already exists")
            raise ResourceAlreadyExistsError(resource="User", identifier=user_create.email)
        
        hashed_password = password_handler.hash_password(user_create.password)
        
        user_data = {
            "email": user_create.email,
            "password_hash": hashed_password
        }
        
        user = self.repository.create(db, user_data)
        logger.info(f"User created successfully with id: {user.id}")
        return user
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        logger.debug(f"Fetching user by email: {email}")
        return self.repository.get_by_email(db, email)
    
    def get_user_by_id(self, db: Session, user_id: str) -> User:
        logger.debug(f"Fetching user by id: {user_id}")
        user = self.repository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(resource="User", identifier=user_id)
        return user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return password_handler.verify_password(plain_password, hashed_password)


user_service = UserService()