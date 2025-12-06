from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.repositories.base import BaseRepository
from app.core.logger import setup_logger
from app.core.exceptions import DatabaseError

logger = setup_logger(__name__)


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                logger.debug(f"User found with email: {email}")
            else:
                logger.debug(f"No user found with email: {email}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user by email: {str(e)}")
            raise DatabaseError(detail="Failed to fetch user by email")
    
    def email_exists(self, db: Session, email: str) -> bool:
        try:
            exists = db.query(User).filter(User.email == email).first() is not None
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Error checking email existence: {str(e)}")
            raise DatabaseError(detail="Failed to check email existence")


user_repository = UserRepository()